# sg-hooked

(c) 2022 Bly Lee d.b.a. WonderGap, LLC

This code is licensed under MIT license

Solely intended for use at Science Gallery: Hooked in ATL, GA in 2022

Software run on Raspberry Pi 4B+ and Arduino Mega2560 and all LEDs are WS2811s

# running/compiling

When running strawberrycough.py, be sure to run with root permissions as the NEOPIXEL library cannot function correctly without them:

`$ sudo ./strawberrycough.py`

When running northernlights.py, it is not necessary to run with root permissions:

`$ ./northernlights.py`

The Arduino program, stardawg.io should be flashed to the Ard memory from a desktop/laptop computer with the Ard IDE, then connected via USB3.0 to the
Raspberry Pi unit.

Should you have issues running the python scripts with the terminal commands above, try:

`$ chmod +x filename.py`

# strawberrycough.py

Strawberrycough.py acts as the showrunner for the in-booth guest experience, controlling all lighting, audio, and DC motors for marble conveyance. Please note, at this time, strawberrycough.py does not support real-time tracking of guest input for use as a data stream for the showcase display. While this functionality could be implemented in a v2.0, it will require the allocation of more resources (predominantly time and money).

**GPIO Pinout (using BCOM/Board numbering)**
 
 GPIO 26 - control for YES button light relay (OUTPUT)
 
 GPIO 20 - control for START button light relay (OUTPUT)
 
 GPIO 25 - control for NO button light relay (OUTPUT)
 
 GPIO 21 - DOUT for LED lighting (OUTPUT)\*
 
 GPIO 16 - START button (INPUT)
 
 GPIO 19 - YES button (INPUT)
 
 GPIO 13 - NO button (INPUT)
 
 GPIO 06 - control for INTERIOR YES DC motor relay (OUTPUT)
 
 GPIO 05 - control for INTERIOR NO DC motor relay (OUTPUT)
 
 GPIO 12 - control for EXTERIOR YES DC motor relay (OUTPUT)
 
 GPIO 07 - control for EXTERIOR NO DC motor relay (OUTPUT)
 
\* While GPIO 18 is the standard PWM OUT for lighting control on the Rapsberry Pi, this PWM channel is shared by the 3.5mm audio jack i.e. it is not possible to play audio over the 3.5mm jack AND control lights at the same time. For this reason, the lights have been switched to GPIO 21 which operates
on an entirely separate PWM channel and causes no interference.

**WS2811 Wiring Instructions**

The NEOPIXEL library on the Raspberry Pi can only handle one strand object at a time i.e. it is not possible to control two separate strands of lights. To workaround this, directly connect 10 question indicator lights to the DOUT on the RPi then daisy-chain the strand to the wheel of accent lights. All the lights can then be treated as one strand where 

`strand[0 ... 9]` controls the question indicator lights and 

`strand[10 ... end]` controls the strand of lights.

RPi GPIO 21 ---> DIN question indicator LED[0] ... LED[9] ---> DOUT ---> DIN strand/wheel of accent lighting


 
 





