#!/usr/bin/env python3

import time
import pygame
from pygame import mixer

#p = vlc.MediaPlayer("intro.mp3")
#p.play()
#pygame.mixer.pre_init(devicename="Built-in Audio Analog Stereo")
#pygame.init()
pygame.mixer.init()
pygame.mixer.music.load('scream.wav')
pygame.mixer.music.play()
time.sleep(3)
pygame.mixer.music.stop()

#sound = mixer.Sound('intro.mp3')
#sound.play()

quit()
