# Collect data and then plot tracks on map on EPD.
# Expects dump1090 to be running locally, ex:
#  dump1090 --raw --net

import time
import random
from datetime import datetime
import requests
import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_epd.uc8179 import Adafruit_UC8179

RUN_TIME = 60 * 60
ALTI_LIMIT = 9500
UPDATE_RATE = 1

BG_FILE = "eng_frame2_map2_480x800.png"
# NW corner
LAT0 = 47.59829
LON0 = -122.63317
# SE corner
LAT1 = 47.23635
LON1 = -122.29156

# this is the sub-region of the full background image
MAP_X = 2
MAP_Y = 2
MAP_WIDTH = 475
MAP_HEIGHT = 705

URL = "http://localhost:8080/data.json"

WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
RED = (255, 0 , 0, 255)

# create the spi device and pins we will need
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
ecs = digitalio.DigitalInOut(board.CE0)
dc = digitalio.DigitalInOut(board.D22)
srcs = None
rst = digitalio.DigitalInOut(board.D27)
busy = digitalio.DigitalInOut(board.D17)

# 7.5" tricolor 800x480 display
display = Adafruit_UC8179(
    800,
    480,
    spi,
    cs_pin=ecs,
    dc_pin=dc,
    sramcs_pin=srcs,
    rst_pin=rst,
    busy_pin=busy,
    tri_color = True)

display.rotation = 3

IMG_WIDTH = display.width
IMG_HEIGHT = display.height

image = Image.new("RGBA", (IMG_WIDTH, IMG_HEIGHT))
bg_img = Image.open(BG_FILE).convert("RGBA")
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("Engplot.TTF", size=12)

# flight (icao hex)
#   last_seen
#   track
#flights = {}

def collect_flights(run_time):
    speed_max = alti_max = total_aircraft = 0
    start_time = time.time()

    while time.time() - start_time < run_time:
        resp = requests.get(URL)
        data = resp.json()

        if len(data):
            print("-"*20)
            now = time.time()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for ac in data:
                icao = ac['hex']
                flight = ac['flight']
                lat = ac['lat']
                lon = ac['lon']
                alt =  ac['altitude']
                speed = ac['speed']
                heading = ac['track']

                # we need an ID
                if len(icao) < 1:
                    print("Skipping. No flight ID.")
                    continue

                # skip high altitude flights
                if alt > ALTI_LIMIT:
                    print("Skipping. Altitude too high:", alt)
                    continue

                print(timestamp, icao, flight, lat, lon, alt, speed, heading)

                # update max's
                speed_max = speed if speed > speed_max else speed_max
                alti_max = alt if alt > alti_max else alti_max

                if icao in flights:
                    # update existing flight
                    flights[icao]['last_seen'] = now
                    flights[icao]['track'].append((lat,lon))
                else:
                    # add new flight
                    flights[icao] = {
                        'last_seen' : now,
                        'track' : [(lat,lon)]
                    }
                    total_aircraft += 1

        time.sleep(UPDATE_RATE)

    end_time = time.time()

    return ({
                'speed_max' : speed_max,
                'alti_max' : alti_max,
                'total_aircraft' : total_aircraft,
                'start_time' : start_time,
                'end_time' : end_time
            })


def plot_flights():
    image.paste(bg_img)

    # plot flights
    for flight in flights:

        width = 4
        color = RED

        track = flights[flight]['track']

        # convert (lat, lon) to (x, y)
        trackxy = []
        for lat, lon in track:
            x = MAP_X + MAP_WIDTH - int(MAP_WIDTH*(lon - LON1) / (LON0 - LON1))
            y = MAP_Y + MAP_HEIGHT - int(MAP_HEIGHT*(lat - LAT1) / (LAT0 - LAT1))
            trackxy.append((x,y))

        # draw tracks
        draw.line(trackxy, color, width, 'curve')

        # draw round end points
        x0, y0 = trackxy[0]
        x1, y1 = trackxy[-1]
        draw.circle((x0,y0), width//2, color)
        draw.circle((x1,y1), width//2, color)

def plot_info(info):
    time_stamp = datetime.fromtimestamp(info['start_time']).strftime("%Y-%m-%d")
    draw.text((160, 724), time_stamp, anchor="lm", align="left", font=font, fill=BLACK)

    time_stamp = datetime.fromtimestamp(info['start_time']).strftime("%H:%M:%S")
    draw.text((167, 754), time_stamp, anchor="lm", align="left", font=font, fill=BLACK)

    time_stamp = datetime.fromtimestamp(info['end_time']).strftime("%H:%M:%S")
    draw.text((161, 785), time_stamp, anchor="lm", align="left", font=font, fill=BLACK)

    draw.text((442, 754), f"{info['speed_max']}", anchor="mm", align="center", font=font, fill=BLACK)
    draw.text((442, 784), f"{info['alti_max']}", anchor="mm", align="center", font=font, fill=BLACK)

    draw.text((299, 784), f"{info['total_aircraft']}", anchor="mm", align="center", font=font, fill=BLACK)


while True:
    flights = {}
    print("collecting...")
    info = collect_flights(RUN_TIME)
    print("plotting...")
    plot_flights()
    plot_info(info)
    display.image(image.convert("RGB"))
    display.display()
    save_file = datetime.now().strftime("%Y%m%d_%H%M%S_epd.png")
    print("saving to:", save_file)
    image.save(save_file)
    print("done.")
