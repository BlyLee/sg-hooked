# sg-hooked

(c) 2022 Bly Lee d.b.a. WonderGap, LLC

This code is licensed under MIT license

Solely intended for use at Science Gallery: Hooked in ATL, GA in 2022

Software run on Raspberry Pi 4B+ and Arduino Mega2560 and all LEDs are WS2811s

# Running/Compiling

When running strawberrycough.py, be sure to run with root permissions as the NEOPIXEL library cannot function correctly without them:

`$ sudo ./strawberrycough.py`

When running northernlights.py, it is not necessary to run with root permissions:

`$ ./northernlights.py`

The Arduino program, stardawg.io should be flashed to the Ard memory from a desktop/laptop computer with the Ard IDE, then connected via USB3.0 to the
Raspberry Pi unit.

Should you have issues running the python scripts with the terminal commands above, try:

`$ chmod +x filename.py`

# strawberrycough.py

