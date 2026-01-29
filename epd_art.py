# Capture lots of data and show as abstract art on EPD.
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
ALTI_LIMIT = 300000
UPDATE_RATE = 1

FRAME_FILE = "picture_frame3.png"

# this is the sub-region within the frame
ART_X = 76
ART_Y = 93
ART_WIDTH = 330
ART_HEIGHT = 510

MIN_WIDTH = 5
MAX_WIDTH = 40

URL = "http://localhost:8080/data.json"

CLEAR = (0,0,0,0)
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
RED = (255, 0 , 0, 255)

f1 = ImageFont.truetype("LiberationSerif-Bold.ttf", size=14)
f2 = ImageFont.truetype("LiberationSerif-Regular.ttf", size=12)
f3 = ImageFont.truetype("LiberationSerif-Italic.ttf", size=12)

fonts = (
    ImageFont.truetype("BigMummy.ttf", size=12),
    ImageFont.truetype("BigMummy.ttf", size=24),
    ImageFont.truetype("BigMummy.ttf", size=48),

    ImageFont.truetype("gomarice_sandome.ttf", size=12),
    ImageFont.truetype("gomarice_sandome.ttf", size=24),
    ImageFont.truetype("gomarice_sandome.ttf", size=48),

    ImageFont.truetype("Subway-Black.ttf", size=12),
    ImageFont.truetype("Subway-Black.ttf", size=24),
    ImageFont.truetype("Subway-Black.ttf", size=48),

    ImageFont.truetype("gomarice_katamari_serif.ttf", size=12),
    ImageFont.truetype("gomarice_katamari_serif.ttf", size=24),
    ImageFont.truetype("gomarice_katamari_serif.ttf", size=48),

    ImageFont.truetype("ZTChintzy-Heavy.ttf", size=12),
    ImageFont.truetype("ZTChintzy-Heavy.ttf", size=24),
    ImageFont.truetype("ZTChintzy-Heavy.ttf", size=48),
)

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

image = Image.new("RGBA", (IMG_WIDTH, IMG_HEIGHT), WHITE)
frame_img = Image.open(FRAME_FILE)
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("Engplot.TTF", size=12)


def collect_flights(run_time):
    total_flights = 0
    lat_min = lon_min = 999
    lat_max = lon_max = -999

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

                # update bounds
                lat_min = lat if lat < lat_min else lat_min
                lat_max = lat if lat > lat_max else lat_max
                lon_min = lon if lon < lon_min else lon_min
                lon_max = lon if lon > lon_max else lon_max

                if icao in flights:
                    # update existing flight
                    flights[icao]['track'].append((lat,lon))
                    if flights[icao]['flight'] is None:
                        flights[icao]['flight'] = flight
                else:
                    # add new flight
                    flights[icao] = {
                        'flight' : flight,
                        'track' : [(lat,lon)]
                    }
                    total_flights += 1

        time.sleep(UPDATE_RATE)

    return (lat_min, lat_max, lon_min, lon_max, total_flights)


def plot_flights(info):
    LAT_MIN = info[0]
    LAT_MAX = info[1]
    LON_MIN = info[2]
    LON_MAX = info[3]
    if LON_MIN==LON_MAX or LAT_MIN==LAT_MAX:
        print("nothing in bounds")
        return

    draw.rectangle([(0,0),(480,800)], WHITE)

    # plot flights
    for icao in flights:

        width = random.randrange(MIN_WIDTH, MAX_WIDTH)
        color = random.choice((BLACK, RED))

        track = flights[icao]['track']

        # convert (lat, lon) to (x, y)
        trackxy = []
        for lat, lon in track:
            x = ART_X + ART_WIDTH - int(ART_WIDTH*(lon - LON_MIN) / (LON_MAX - LON_MIN))
            y = ART_Y + ART_HEIGHT - int(ART_HEIGHT*(lat - LAT_MIN) / (LAT_MAX - LAT_MIN))
            trackxy.append((x,y))

        # draw tracks
        draw.line(trackxy, color, width, 'curve')

        # draw round end points
        x0, y0 = trackxy[0]
        x1, y1 = trackxy[-1]
        draw.circle((x0,y0), width//2, color)
        draw.circle((x1,y1), width//2, color)

        # # flight text label
        # text = flights[icao]['flight']
        # font = random.choice(fonts)
        # fill = random.choice((BLACK, RED, WHITE))
        # stroke_fill = fill
        # while stroke_fill == fill:
        #     stroke_fill = random.choice((BLACK, RED, WHITE))
        # stroke_width = random.randrange(2,8)
        # rotation = random.randrange(360)

        # bbox = font.getbbox(text)  # returns (left, top, right, bottom) bounding box
        # box_width = bbox[2] - bbox[0]
        # box_height = bbox[3] - bbox[1]
        # #print(text, bbox, box_width, box_height)

        # label_img = Image.new("RGBA", (box_width, box_height), CLEAR)
        # label_draw = ImageDraw.Draw(label_img)
        # label_draw.text((0,0), text, anchor='lt', font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        # label_img = label_img.rotate(rotation, expand=True)

        # XO = label_img.width // 2
        # YO = label_img.height // 2
        # location = (
        #     random.randrange(ART_X, ART_X + ART_WIDTH) - XO,
        #     random.randrange(ART_Y, ART_Y + ART_HEIGHT) - YO
        # )

        # image.paste(label_img, location, mask=label_img)

def add_label(info):
    draw.rectangle([(266,710),(466,790)], fill=WHITE, outline=BLACK, width=3)
    draw.text((271, 714), "Aydee Esbi", fill=BLACK, font=f1)
    draw.text((271, 728), "21st century, Earth.", fill=BLACK, font=f2)

    draw.text((271, 743), f"Saw {info} airplanes.", fill=BLACK, font=f1)
    draw.text((271, 757), datetime.now().strftime("%Y-%m-%d"), fill=BLACK, font=f2)

    draw.text((271, 775), "eink on electrical substrate", fill=BLACK, font=f3)

while True:
    flights = {}
    print("collecting...")
    info = collect_flights(RUN_TIME)
    print("info=",info)
    print("plotting...")
    plot_flights(info)
    image.paste(frame_img, mask=frame_img)
    add_label(info[-1])
    display.image(image.convert("RGB"))
    display.display()
    save_file = datetime.now().strftime("%Y%m%d_%H%M%S_epd_art.png")
    print("saving to:", save_file)
    image.save(save_file)
    print("done.")


