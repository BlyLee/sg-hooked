#!/usr/bin/env python3

# (c) 2022 Bly Lee d.b.a. WonderGap, LLC
# This code is licensed under MIT license
# Solely intended for use at Science Gallery: Hooked in ATL, GA in 2022

import sys
import os
import subprocess
import psutil
import time
import signal
import RPi.GPIO as GPIO
import serial
import neopixel
import board
import pygame
from multiprocessing import Process
from pygame import mixer

# constant global value used for sleep(value) when motors are turned on after each question
# increase/decrease as needed with testing for appropriate marble conveyance
MOTOR_DELAY = 5

# do not need to initialize pygame, doing so will cause loss of video feed to terminal
pygame.mixer.init()

# WS2811s must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D21

# number of lights/chips
# ~100 for the strand + 10 for the LED question indicators (includes spare)
num_pixels = 110

# order of the pixel colors - RGB or GRB
# for RGBW NeoPixels, simply change the ORDER to RGBW or GRBW
ORDER = neopixel.GRB

# setup strand of WS2811s using Neopixel library
pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.5, auto_write=False, pixel_order=ORDER
)

# stop consol readout of harmless GPIO warnings
GPIO.setwarnings(False)

# refer to pins by Broacom SOC Channel instead of board numbers (GPIO# in $pinout terminal command)
GPIO.setmode(GPIO.BCM)

# define relays for Button input and DC motor relays
# GPIO pins 2 and 4 are being used for the onboard RTC module
btnStart = 16
btnYes = 19
btnNo = 13

# relays for controling button lights
startRelay = 20
yesRelay = 26
noRelay = 25

# int = interior; ext = exterior
motorIntYes = 6
motorIntNo = 5
motorExtYes = 12
motorExtNo = 7

# assign GPIO mode
GPIO.setup(btnStart, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin to an input pin and set initial value to be pulled low (off)
GPIO.setup(btnYes, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(btnNo, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.setup(startRelay, GPIO.OUT)
GPIO.setup(yesRelay, GPIO.OUT)
GPIO.setup(noRelay, GPIO.OUT)

GPIO.setup(motorIntYes, GPIO.OUT)
GPIO.setup(motorIntNo, GPIO.OUT)
GPIO.setup(motorExtYes, GPIO.OUT)
GPIO.setup(motorExtNo, GPIO.OUT)

# ensure all relays begin in off position
GPIO.output(startRelay, GPIO.LOW)
GPIO.output(yesRelay, GPIO.LOW)
GPIO.output(noRelay, GPIO.LOW)
GPIO.output(motorIntYes, GPIO.LOW)
GPIO.output(motorIntNo, GPIO.LOW)
GPIO.output(motorExtYes, GPIO.LOW)
GPIO.output(motorExtNo, GPIO.LOW)

# helper function for rainbow_cycle and rainbow_cycle_questions
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

# generates rainbow cycle of colors on LED strand but NOT on the question indicator lights
def rainbow_cycle(wait):
    for j in range(255):
        for i in range(10, num_pixels):
            pixel_index = (i * 256 // (num_pixels-10)) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

# generates rainbow cycle of colors on LED strand AND LED question indicators
def rainbow_cycle_questions(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

# fun effect for emphasis, change 2nd arguement if different color desired
def theaterChase(strip, color, wait_ms=50, iterations=10):
    for j in range(iterations):
        for q in range(3):
            for i in range(0, 108, 3):
                strip[i+q] = color
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, 108, 3):
                strip[i+q] = (0, 0, 0)

#initial preshow settings
GPIO.add_event_detect(16, GPIO.RISING, bouncetime=5000)
GPIO.output(startRelay, GPIO.HIGH)
while True:
    # wait for start button press
    rainbow_cycle_questions(0.001)
    if GPIO.event_detected(16):
        GPIO.remove_event_detect(16)
        GPIO.output(startRelay, GPIO.LOW)
        pygame.mixer.music.load('buttonpress.mp3')
        pygame.mixer.music.play()
        theaterChase(pixels, (255, 255 , 255))
        rainbow_cycle_questions(0.001)
        break
# play intro audio
pygame.mixer.music.load('intro.mp3')
pygame.mixer.music.play()
while pygame.mixer.music.get_busy():
    rainbow_cycle_questions(0.001)
# ensure all question indicator LEDs are off
for i in range (10):
   pixels[i] = (0,0,0)
   pixels.show()
# turn on first question indicator LED
pixels[0] = (255,255,255)
pixels.show()
# play question 1
pygame.mixer.music.load('q1.mp3')
pygame.mixer.music.play()
# turn on lights for YES and NO buttons and begin event listening
GPIO.add_event_detect(19, GPIO.RISING, bouncetime=5000)
GPIO.output(yesRelay, GPIO.HIGH)
GPIO.add_event_detect(13, GPIO.RISING, bouncetime=5000)
GPIO.output(noRelay, GPIO.HIGH)
# start timer for question timeout
epoch = time.time()
# encapsulate question in try/catch so that StopIteration exception can be used to break out of nested loops
try:
    while True:
       # give 45 seconds per question before timeout and game reset
        while time.time() - epoch <= 45:
            # give 30 seconds per question before warning sound plays
            while time.time() - epoch <= 30:
                # cycle rainbows (only on LED strand) while waiting for response
                rainbow_cycle(0.001)
                # if yes
                if GPIO.event_detected(19):
               	    # stop any currently playing sounds in case guest hits button before question audio ends
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    # turn off event detect and YES, NO button lights
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    # fun lights and motors for interior and exterior marble runs
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    # pause to give time for marble conveyance
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    # motors off
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    # force exit outer 'while True' loop to continue with program
                    raise StopIteration
                # if no
                if GPIO.event_detected(13):
                    # stop any currently playing sounds in case guest hits button before question audio ends
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    # turn off event detect and YES, NO button lights
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
               	    GPIO.remove_event_detect(13)
               	    GPIO.output(noRelay, GPIO.LOW)
               	    # fun lights and motors for interior and exterior marble runs
                    theaterChase(pixels, (255, 255 , 255))
               	    GPIO.output(motorIntYes, GPIO.HIGH)
               	    GPIO.output(motorExtYes, GPIO.HIGH)
               	    # pause to give time for marble conveyance
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    # motors off
               	    GPIO.output(motorIntYes, GPIO.LOW)
               	    GPIO.output(motorExtYes, GPIO.LOW)
               	    # force exit outer 'while True' loop to continue with program
                    raise StopIteration
            # play warning audio after 30 seconds of inactivity
            pygame.mixer.music.load('inactivitywarning.mp3')
            pygame.mixer.music.play()
            # continue listening while warning audio plays
            while pygame.mixer.music.get_busy():
                if GPIO.event_detected(19):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW) 
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                time.sleep(10)
            time.sleep(0.01)
        #restart program due to timeout on question (< 45 seconds)
        os.execv(__file__, sys.argv)
# handle StopIteration exception
except StopIteration:
    pass
# repeat exact same logic for questions 2-9
# question 2
pixels[1] = (255,255,255)
pixels.show()
rainbow_cycle(0.001)
pygame.mixer.music.load('q2.mp3')
pygame.mixer.music.play()
GPIO.add_event_detect(19, GPIO.RISING, bouncetime=5000)
GPIO.output(yesRelay, GPIO.HIGH)
GPIO.add_event_detect(13, GPIO.RISING, bouncetime=5000)
GPIO.output(noRelay, GPIO.HIGH)
epoch = time.time()
try:
    while True:
        while time.time() - epoch <= 45:
            while time.time() - epoch <= 30:
                rainbow_cycle(0.001)
                if GPIO.event_detected(19):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
            pygame.mixer.music.load('inactivitywarning.mp3')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if GPIO.event_detected(19):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW) 
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                time.sleep(10)
            time.sleep(0.01)
        #restart program due to timeout on question
        os.execv(__file__, sys.argv)
except StopIteration:
    pass
# repeat exact same logic for questions 2-9
# question 3
pixels[2] = (255,255,255)
pixels.show()
rainbow_cycle(0.001)
pygame.mixer.music.load('q3.mp3')
pygame.mixer.music.play()
GPIO.add_event_detect(19, GPIO.RISING, bouncetime=5000)
GPIO.output(yesRelay, GPIO.HIGH)
GPIO.add_event_detect(13, GPIO.RISING, bouncetime=5000)
GPIO.output(noRelay, GPIO.HIGH)
epoch = time.time()
try:
    while True:
        while time.time() - epoch <= 45:
            while time.time() - epoch <= 30:
                rainbow_cycle(0.001)
                if GPIO.event_detected(19):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
            pygame.mixer.music.load('inactivitywarning.mp3')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if GPIO.event_detected(19):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW) 
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                time.sleep(10)
            time.sleep(0.01)
        #restart program due to timeout on question
        os.execv(__file__, sys.argv)
except StopIteration:
    pass
# repeat exact same logic for questions 2-9
# question 4
pixels[3] = (255,255,255)
pixels.show()
rainbow_cycle(0.001)
pygame.mixer.music.load('q4.mp3')
pygame.mixer.music.play()
GPIO.add_event_detect(19, GPIO.RISING, bouncetime=5000)
GPIO.output(yesRelay, GPIO.HIGH)
GPIO.add_event_detect(13, GPIO.RISING, bouncetime=5000)
GPIO.output(noRelay, GPIO.HIGH)
epoch = time.time()
try:
    while True:
        while time.time() - epoch <= 45:
            while time.time() - epoch <= 30:
                rainbow_cycle(0.001)
                if GPIO.event_detected(19):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
            pygame.mixer.music.load('inactivitywarning.mp3')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if GPIO.event_detected(19):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW) 
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                time.sleep(10)
            time.sleep(0.01)
        #restart program due to timeout on question
        os.execv(__file__, sys.argv)
except StopIteration:
    pass
# repeat exact same logic for questions 2-9
# question 5
pixels[4] = (255,255,255)
pixels.show()
rainbow_cycle(0.001)
pygame.mixer.music.load('q5.mp3')
pygame.mixer.music.play()
GPIO.add_event_detect(19, GPIO.RISING, bouncetime=5000)
GPIO.output(yesRelay, GPIO.HIGH)
GPIO.add_event_detect(13, GPIO.RISING, bouncetime=5000)
GPIO.output(noRelay, GPIO.HIGH)
epoch = time.time()
try:
    while True:
        while time.time() - epoch <= 45:
            while time.time() - epoch <= 30:
                rainbow_cycle(0.001)
                if GPIO.event_detected(19):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
            pygame.mixer.music.load('inactivitywarning.mp3')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if GPIO.event_detected(19):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW) 
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                time.sleep(10)
            time.sleep(0.01)
        #restart program due to timeout on question
        os.execv(__file__, sys.argv)
except StopIteration:
    pass
# repeat exact same logic for questions 2-9
# question 6
pixels[5] = (255,255,255)
pixels.show()
rainbow_cycle(0.001)
pygame.mixer.music.load('q6.mp3')
pygame.mixer.music.play()
GPIO.add_event_detect(19, GPIO.RISING, bouncetime=5000)
GPIO.output(yesRelay, GPIO.HIGH)
GPIO.add_event_detect(13, GPIO.RISING, bouncetime=5000)
GPIO.output(noRelay, GPIO.HIGH)
epoch = time.time()
try:
    while True:
        while time.time() - epoch <= 45:
            while time.time() - epoch <= 30:
                rainbow_cycle(0.001)
                if GPIO.event_detected(19):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
            pygame.mixer.music.load('inactivitywarning.mp3')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if GPIO.event_detected(19):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW) 
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                time.sleep(10)
            time.sleep(0.01)
        #restart program due to timeout on question
        os.execv(__file__, sys.argv)
except StopIteration:
    pass
# repeat exact same logic for questions 2-9
# question 7
pixels[6] = (255,255,255)
pixels.show()
rainbow_cycle(0.001)
pygame.mixer.music.load('q7.mp3')
pygame.mixer.music.play()
GPIO.add_event_detect(19, GPIO.RISING, bouncetime=5000)
GPIO.output(yesRelay, GPIO.HIGH)
GPIO.add_event_detect(13, GPIO.RISING, bouncetime=5000)
GPIO.output(noRelay, GPIO.HIGH)
epoch = time.time()
try:
    while True:
        while time.time() - epoch <= 45:
            while time.time() - epoch <= 30:
                rainbow_cycle(0.001)
                if GPIO.event_detected(19):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
            pygame.mixer.music.load('inactivitywarning.mp3')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if GPIO.event_detected(19):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW) 
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                time.sleep(10)
            time.sleep(0.01)
        #restart program due to timeout on question
        os.execv(__file__, sys.argv)
except StopIteration:
    pass
# repeat exact same logic for questions 2-9
# question 8
pixels[7] = (255,255,255)
pixels.show()
rainbow_cycle(0.001)
pygame.mixer.music.load('q8.mp3')
pygame.mixer.music.play()
GPIO.add_event_detect(19, GPIO.RISING, bouncetime=5000)
GPIO.output(yesRelay, GPIO.HIGH)
GPIO.add_event_detect(13, GPIO.RISING, bouncetime=5000)
GPIO.output(noRelay, GPIO.HIGH)
epoch = time.time()
try:
    while True:
        while time.time() - epoch <= 45:
            while time.time() - epoch <= 30:
                rainbow_cycle(0.001)
                if GPIO.event_detected(19):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
            pygame.mixer.music.load('inactivitywarning.mp3')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if GPIO.event_detected(19):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW) 
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                time.sleep(10)
            time.sleep(0.01)
        #restart program due to timeout on question
        os.execv(__file__, sys.argv)
except StopIteration:
    pass
# repeat exact same logic for questions 2-9
# question 9
pixels[8] = (255,255,255)
pixels.show()
rainbow_cycle(0.001)
pygame.mixer.music.load('q9.mp3')
pygame.mixer.music.play()
GPIO.add_event_detect(19, GPIO.RISING, bouncetime=5000)
GPIO.output(yesRelay, GPIO.HIGH)
GPIO.add_event_detect(13, GPIO.RISING, bouncetime=5000)
GPIO.output(noRelay, GPIO.HIGH)
epoch = time.time()
try:
    while True:
        while time.time() - epoch <= 45:
            while time.time() - epoch <= 30:
                rainbow_cycle(0.001)
                if GPIO.event_detected(19):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
            pygame.mixer.music.load('inactivitywarning.mp3')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if GPIO.event_detected(19):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW)
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                if GPIO.event_detected(13):
                    GPIO.remove_event_detect(19)
                    GPIO.output(yesRelay, GPIO.LOW)
                    GPIO.remove_event_detect(13)
                    GPIO.output(noRelay, GPIO.LOW) 
                    theaterChase(pixels, (255, 255 , 255))
                    GPIO.output(motorIntYes, GPIO.HIGH)
                    GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(MOTOR_DELAY)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                time.sleep(10)
            time.sleep(0.01)
        #restart program due to timeout on question
        os.execv(__file__, sys.argv)
except StopIteration:
    pass
# play final sound clip and restart program
rainbow_cycle_questions(0.001)
pygame.mixer.music.load('finale.mp3')
pygame.mixer.music.play()
while pygame.mixer.music.get_busy():
    rainbow_cycle_questions(0.001)
rainbow_cycle_questions(0.001)

#restart program
pygame.quit()
GPIO.cleanup()
os.execv(__file__, sys.argv)
