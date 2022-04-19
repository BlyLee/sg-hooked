#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple test for NeoPixels on Raspberry Pi
import time
import board
import neopixel
import time
import RPi.GPIO as GPIO

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 110

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)

GPIO.setmode(GPIO.BCM) #refer to pins by GPIO pin numbers
GPIO.setwarnings(False) #removes harmless "RuntimeWarning: This channel is already in use..."

RELAY1 = 26
RELAY2 = 20
RELAY3 = 21

GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.setup(RELAY1, GPIO.OUT) # GPIO Assign mode
GPIO.setup(RELAY2, GPIO.OUT)
GPIO.setup(RELAY3, GPIO.OUT)

GPIO.output(RELAY1, GPIO.LOW) #ensure all relays begin in off position
GPIO.output(RELAY2, GPIO.LOW)
GPIO.output(RELAY3, GPIO.LOW)

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)


def rainbow_cycle(wait):
    for j in range(255):
        for i in range(10, num_pixels):
            pixel_index = (i * 256 // (num_pixels-10)) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

def start(channel):
     print("start was pushed")

GPIO.add_event_detect(16, GPIO.RISING, callback=start)

while True:
    #if GPIO.input(16) == GPIO.HIGH:
        #print("Start was pushed!")

    # Comment this line out if you have RGBW/GRBW NeoPixels
    pixels.fill((255, 0, 0))
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((255, 0, 0, 0))
    pixels.show()
    GPIO.output(RELAY1, GPIO.HIGH)
    time.sleep(1)

    # Comment this line out if you have RGBW/GRBW NeoPixels
    pixels.fill((0, 255, 0))
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((0, 255, 0, 0))
    GPIO.output(RELAY1, GPIO.LOW) 
    GPIO.output(RELAY2, GPIO.HIGH)
    pixels.show()
    time.sleep(1)

    # Comment this line out if you have RGBW/GRBW NeoPixels
    pixels.fill((0, 0, 255))
    # Uncomment this line if you have RGBW/GRBW NeoPixels
    # pixels.fill((0, 0, 255, 0))
    GPIO.output(RELAY2, GPIO.LOW)
    GPIO.output(RELAY3, GPIO.HIGH)
    pixels.show()
    time.sleep(1)

    pixels[0] = (255, 0, 0)
    pixels[10] = (255, 0, 0)
    pixels.show()
    time.sleep(10)
    GPIO.output(RELAY1, GPIO.LOW)
    GPIO.output(RELAY2, GPIO.LOW)
    GPIO.output(RELAY3, GPIO.LOW)
    rainbow_cycle(0.001)  # rainbow cycle with 1ms delay per step


