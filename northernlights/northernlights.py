#!/usr/bin/env python3

# (c) 2022 Bly Lee d.b.a. WonderGap, LLC
# This code is licensed under MIT license
# Solely intended for use at Science Gallery: Hooked in ATL, GA in 2022

import time
import datetime
import SDL_DS3231
import serial

# initialize values
m = 0

# initialize clock
ds3231 = SDL_DS3231.SDL_DS3231(1, 0x68)

if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser.reset_input_buffer()

while True:
    # read current minutes
    m = time.strftime("%M")
    if (m == "00"):
        #send serial signal
        ser.write(1)
    else:
        ser.write(0)
    # wait 60 seconds to check minute value again
    time.sleep(60)
