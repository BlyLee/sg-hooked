#!/usr/bin/env python3

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

pygame.mixer.init()

# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D21

# The number of NeoPixels
# ~100 for the strand + 10 for the LED question indicators (includes spare)
num_pixels = 110

# The order of the pixel colors - RGB or GRB
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.5, auto_write=False, pixel_order=ORDER
)

GPIO.setwarnings(False)

# refer to pins by Broacom SOC Channel instead of board numbers (GPIO# in $pinout terminal command)
GPIO.setmode(GPIO.BCM)

# define relays for Button input and DC motor relays
# GPIO pins 2 and 4 are being used for the onboard RTC module
btnStart = 16
btnYes = 19
btnNo = 13

startRelay = 20
yesRelay = 26
noRelay = 25

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

def rainbow_cycle_questions(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

def theaterChase(strip, color, wait_ms=50, iterations=10):
    for j in range(iterations):
        for q in range(3):
            for i in range(0, 108, 3):
                strip[i+q] = color
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, 108, 3):
                strip[i+q] = (0, 0, 0)

def end_exp():
    # play final audio
    cmdFinal = "omxplayer %s " % (final)
    spFinal = subprocess.Popen(
        cmdFinal, shell=True, stdin=subprocess.PIPE, stdout=FNULL, stderr=FNULL)
    # wait for audio to end
    while spFinal.poll() is None:
        time.sleep(0.5)
    return


def no(channel):
    # kill any remaining audio
    procs = getplayers()
    killoldplayers(procs)
    # play audio for y/n button press
    cmdButtonPress = "omxplayer %s " % (buttonpress)
    spButtonPress = subprocess.Popen(
        cmdButtonPress, shell=True, stdin=subprocess.PIPE, stdout=FNULL, stderr=FNULL)
    # activate correct motors
    GPIO.output(MOTORINTNO, GPIO.HIGH)
    GPIO.output(MOTOREXTNO, GPIO.HIGH)
    time.sleep(20)
    GPIO.output(MOTORINTNO, GPIO.LOW)
    GPIO.output(MOTOREXTNO, GPIO.LOW)


def yes(channel):
    # turn off event detection
    GPIO.remove_event_detect(19)
    GPIO.remove_event_detect(13)
    # TO DO
    #set_tracker(0)
    print('yes button pressed')
    # kill any remaining audio
    pygame.mixer.music.stop()
    # play audio for y/n button press
    pygame.mixer.music.load('buttonpress.mp3')
    pygame.mixer.music.play()
    # activate correct motors
    GPIO.output(motorIntYes, GPIO.HIGH)
    GPIO.output(motorExtYes, GPIO.HIGH)
    time.sleep(5)
    GPIO.output(motorIntYes, GPIO.LOW)
    GPIO.output(motorExtYes, GPIO.LOW)
    #set_tracker(4)
    return

def question(i):
    global state_tracker
    state_tracker = i + 2
    # turn on yes/no buttons for event detection
    GPIO.add_event_detect(19, GPIO.RISING, bouncetime=5000)
    GPIO.add_event_detect(13, GPIO.RISING, bouncetime=5000)
    epoch = time.time()
    # play question audio
    track = 'q' + str(i) + '.mp3'
    #pygame.mixer.music.unload()
    pygame.mixer.music.load(track)
    pygame.mixer.music.play()
    # wait until audio stops playing
    # wait for yes or no input
    while time.time()-epoch < 45:
        #print(time.time()-epoch)
        if GPIO.event_detected(19):
            print('yes pressed')
            return
        if GPIO.event_detected(13):
            return
        if time.time()-epoch > 30:
            print('inactivitywarning')
            pygame.mixer.music.load('inactivitywarning.mp3')
            pygame.mixer.music.play()
    else:
        # restart program due to timeout on question
        os.execv(__file__, sys.argv)


def begin_exp(channel):
    global state_tracker
    state_tracker = 1
    print("start was pushed")
    # turn off event detection for start button
    GPIO.remove_event_detect(16)
    # turn off start button light
    GPIO.output(startRelay, GPIO.LOW)
    # play intro audio
    pygame.mixer.music.load('intro.mp3')
    pygame.mixer.music.play()
    return

def set_tracker(x):
    global state_tracker
    state_tracker = x

def cleanup():
    #turn off all relays and lights, turn off any event detection we don't want
    GPIO.cleanup()
    return


#initial preshow settings
GPIO.add_event_detect(16, GPIO.RISING, bouncetime=5000)
GPIO.output(startRelay, GPIO.HIGH)
while True:
    rainbow_cycle_questions(0.001)
    if GPIO.event_detected(16):
        GPIO.remove_event_detect(16)
        GPIO.output(startRelay, GPIO.LOW)
        pygame.mixer.music.load('buttonpress.mp3')
        pygame.mixer.music.play()
        theaterChase(pixels, (255, 255 , 255))
        rainbow_cycle_questions(0.001)
        break
pygame.mixer.music.load('intro.mp3')
pygame.mixer.music.play()
while pygame.mixer.music.get_busy():
    rainbow_cycle_questions(0.001)
#rainbow_cycle_questions(0.001)
print('point A')
for i in range (10):
   pixels[i] = (0,0,0)
   pixels.show()
pixels[0] = (255,255,255)
pixels.show()
print('point B')
pygame.mixer.music.load('q1.mp3')
print('point C')
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
                    #GPIO.output(motorExtYes, GPIO.HIGH)
                    rainbow_cycle(0.001)
                    time.sleep(5)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    #GPIO.output(motorExtYes, GPIO.LOW)
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
               	    time.sleep(5)
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
                    time.sleep(5)
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
                    time.sleep(5)
                    GPIO.output(motorIntYes, GPIO.LOW)
                    GPIO.output(motorExtYes, GPIO.LOW)
                    raise StopIteration
                time.sleep(10)
            time.sleep(0.01)
        #restart program due to timeout on question
        os.execv(__file__, sys.argv)
except StopIteration:
    print('stop iteration is slow')
    pass
print('escaped the loop')
pixels[1] = (255,255,255)
pixels.show()
rainbow_cycle(0.001)
pygame.mixer.music.load('q2.mp3')
pygame.mixer.music.play()
GPIO.add_event_detect(19, GPIO.RISING, bouncetime=5000)
GPIO.output(yesRelay, GPIO.HIGH)
GPIO.add_event_detect(13, GPIO.RISING, bouncetime=5000)
GPIO.output(noRelay, GPIO.HIGH)
print('YOU MADE IT')
while pygame.mixer.music.get_busy():
    rainbow_cycle(0.001)
rainbow_cycle(0.001)
