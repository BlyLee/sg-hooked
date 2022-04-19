#!/usr/bin/env python3

import board
import neopixel

pixels = neopixel.NeoPixel(board.D18, 50)

pixels[0] = (255, 0, 0)


while True:
	pixels[1] = (0, 255, 255)
