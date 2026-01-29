# Show aircraft locations on RGB matrix.
# Expects dump1090 to be running locally, ex:
#  dump1090 --raw --net

import time
import random
from datetime import datetime
import requests
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# NW corner
LAT0 = 47.712903
LON0 = -122.628291
# SE corner
LAT1 = 47.161006
LON1 = -122.202890

KEEP_ALIVE = 60
TAIL_LENGTH = 10

URL = "http://localhost:8080/data.json"
MATRIX_WIDTH = 32
MATRIX_HEIGHT = 64

options = RGBMatrixOptions()

options.hardware_mapping = 'adafruit-hat'
options.rows = MATRIX_WIDTH
options.cols = MATRIX_HEIGHT
options.pixel_mapper_config = 'Rotate:90'

matrix = RGBMatrix(options = options)

# flight
#   last_seen
#   track_color
#   track
tracks = {}

def get_track_color():
    head_color = (0, 0, 0)
    while 255 not in head_color:
        r = random.choice((0, 255))
        g = random.choice((0, 255))
        b = random.choice((0, 255))
        head_color = (r, g, b)

    r = int(0.3 * r)
    g = int(0.3 * g)
    b = int(0.3 * b)

    tail_color = (r, g, b)

    return head_color, tail_color

def plot_tracks():
    now = time.time()
    to_delete = []
    matrix.Clear()
    # loop over each entry (aircraft)
    for flight in tracks:
        # mark for deletion if old
        if now - tracks[flight]['last_seen'] > KEEP_ALIVE:
            to_delete.append(flight)
            continue

        # otherwise plot
        track = tracks[flight]['track']
        head_color, tail_color = tracks[flight]['track_color']
        # plot head
        x, y = track[-1]
        matrix.SetPixel(x, y, *head_color)
        # plot tail
        for x, y in track[:-1]:
            matrix.SetPixel(x, y, *tail_color)

    # remove old tracks
    for flight in to_delete:
        print("Removed:", flight)
        del tracks[flight]

print("looping...")
while True:
    resp = requests.get(url = URL)
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

            # we need an ID
            if len(flight) < 1:
                print("Skipping. No flight ID.")
                continue

            x = 31 - int(31*(lon - LON1) / (LON0 - LON1))
            y = 63 - int(63*(lat - LAT1) / (LAT0 - LAT1))

            print(timestamp, icao, flight, lat, lon, alt, x, y)

            if x in range(MATRIX_WIDTH) and y in range(MATRIX_HEIGHT):
                if flight in tracks:
                    # update time last seen
                    tracks[flight]['last_seen'] = now
                    # add new point if changed
                    last_x, last_y = tracks[flight]['track'][-1]
                    if x != last_x or y != last_y:
                        tracks[flight]['track'].append((x,y))
                        # trim if needed
                        if len(tracks[flight]['track']) > TAIL_LENGTH:
                            del tracks[flight]['track'][0]
                else:
                    # add new track
                    tracks[flight] = {
                        'last_seen' : now,
                        'track_color' : get_track_color(),
                        'track' : [(x,y)]
                    }

    plot_tracks()

    time.sleep(1)
