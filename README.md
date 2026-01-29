# RPi_ADSB_SDR_Displays
Various displays of aircraft ADS-B data obtained via SDR on Raspberry Pi.


# Requirements
* Raspberry Pi
* An SDR supported by dump1090, [like this one](https://www.adafruit.com/product/1497)
* dump1090
* For RGB Matrix display:
  * [RGB Matrix Bonnet](https://www.adafruit.com/product/3211)
  * [64x32 RGB Matrix](https://www.adafruit.com/product/2278)
* For EPD display:
  * [EPD Bonnet](https://www.adafruit.com/product/6418)
  * [7.5" Tri-Color eInk](https://www.adafruit.com/product/6415)
* [Blinka](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi) setup with support libraries for the above h/w installed.


# Install dump1090
This can be done by cloning the [source code repo](https://github.com/antirez/dump1090)
directly onto the pi and running `make`. May need to apt install some deps, like librtlsdr.

Once built, run with:
```
dump1090 --raw --net
```
and then JSON data can be reached at `http://localhost:8080/data.json`.

Example JSON data return:
```
[
{"hex":"a8103e", "flight":"ASA61   ", "lat":47.397254, "lon":-122.506150, "altitude":11675, "track":313, "speed":319}
]
```
There will be an entry for each a/c found.

