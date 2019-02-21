#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

""" huetemperature.py reads temperature values from DS18B20 sensor 
    and writes the current temperature to a 4-digit 7-segment display.
    It also adjusts the color of a Philips Hue lamp to indicate 
    the current temperature. 
    
    By default the colour becomes reddish when cold and bluish when hot. 
    
    Temperatures are adjusted for Southern Finland climate. 
""" 

import time 
import RPi.GPIO as IO 
import urllib.request
import asyncio 
import concurrent.futures 
from settings import SENSOR_FILE_PATH, LAMP_URL


# One writer function writes and reader(s) read this global value.  
TEMPERATURE = 0 

# This maps the temperatures to certain shades of light colour 
# The colours are discrete to make it easier to estimate the temperature.  
# Refer to HUE documentation or use HUE's REST API to test these.
tempToColour = {
     35.0:[0.279,0.3171],
     30.0:[0.292,0.3212],
     25.0:[0.3042,0.3291],
     20.0:[0.3101,0.3438],
     15.0:[0.3236,0.3438],
     10.0:[0.3327,0.3472],
     -5.0:[0.3777,0.3847],
    -10.0:[0.4371,0.4311],
    -15.0:[0.4797,0.4173],
    -25.0:[0.5205,0.4152],
    -99.0:[0.5535,0.412]
}


# This maps each of the display's four digits to activation GPIO pins. 
# This is my wiring. 
digitToPins = {
    1: 31, 
    2: 33, 
    3: 35, 
    4: 29 
}


# This maps the seven segments (plus dot) of each digit to GPIO pins. 
# This is my wiring. 
segmentsToPins = {
    1: 32, # top line 
    2: 36, # Upper left 
    3: 38, # Upper right 
    4: 22, # middle line 
    5: 11, # Lower left 
    6: 18, # Lower right 
    7: 15, # bottom line 
    8: 16  # dot
}


# This tells how to draw characters and numbers in terms of segments. 
characterToSegments = {
    ' ': [], 
    '1': [3, 6], 
    '2': [1, 3, 4, 5, 7], 
    '3': [1, 3, 4, 6, 7], 
    '4': [2, 3, 4, 6], 
    '5': [1, 2, 4, 6, 7], 
    '6': [1, 2, 4, 5, 6, 7], 
    '7': [1, 3, 6], 
    '8': [1, 2, 3, 4, 5, 6, 7], 
    '9': [1, 2, 3, 4, 6, 7], 
    '0': [1, 2, 3, 5, 6, 7], 
    '.': [8],
    '-': [4], 
    'E': [1, 2, 4, 5, 7], 
    'r': [4, 5]
}


# Prints a single digit on the display at index "index". 
# This is called repeatedly, very fast. 
# By drawing digits tens of times each second we create 
# an illusion of permanent text.  
def _print_char(index, char):
    for i in range(1,9): 
        # Wipe digit 
        IO.output(segmentsToPins[i],1) 

    for s in characterToSegments[char]: 
        # Now we go through the list of segments and ground 
        # (remember, common cathode) its respective output pin: 
        IO.output(segmentsToPins[s],0) 
        if index == 3: 
            # Add dot in position three 
            IO.output(segmentsToPins[8],0) 

    IO.output(digitToPins[index], 1) # Enable digit at index 
    time.sleep(0.005) # We let is shine only very briefly. 
    IO.output(digitToPins[index], 0) # Disable digit at index 


# This is wrapped inside a thread because it talks to display synchronously
def _print_temperature():
    global TEMPERATURE
    while True: 
        temp = TEMPERATURE 
        digits = ''
        if -10 < temp < 10:
            digits += ' ' # Padding for single digit numbers 

        if temp < 0: 
            digits += '-'  # Add minus sign and remove it from the number 
            temp = TEMPERATURE * -1
        else: 
            digits += ' ' # No minus sign, so put padding instead to keep positions consistent

        if temp >= 100: 
            digits = "Err " # Display at most two digits before dot, signal an error

        digits += str(temp).replace('.', '') # Remove dot, it's always put after third number

        for i, digit in enumerate(digits[:4]):
            _print_char(i+1, digit)


# Changes the colour of the lamp. 
def _set_lamp_colour():
    global TEMPERATURE
    url = LAMP_URL
    while True: 
        for k, v in tempToColour.items(): 
            # Temperatures are in descending order. 
            if TEMPERATURE > k: 
                try: 
                    body = '{"xy":%s}' % v
                    request = urllib.request.Request(url, body.encode(), method='PUT')
                    with urllib.request.urlopen(request) as response: 
                        pass 
                    break
                except Exception as e: 
                    pass 
        time.sleep(LAMP_UPDATE_INTERVAL)


def _read_temperature(): 
    global TEMPERATURE
    while True: 
        temperaturefile = None 
        try: 
            temperaturefile = open(SENSOR_FILE_PATH)
            data = temperaturefile.read()
            temperaturefile.seek(0)
            tdata = data.split("\n")[1].split(" ")[9]
            temperature = float(tdata[2:])
            TEMPERATURE = temperature / 1000 
        except FileNotFoundError: 
            #TODO: Print error in logs. Also change handling on digits so that 
            # Also texts can be printed with printing function.
            TEMPERATURE = 100 # value 100 causes printing "Err"
        finally: 
            if temperaturefile is not None:  
                temperaturefile.close()

        # See settings.py 
        time.sleep(TEMPERATURE_UPDATE_INTERVAL) 


# Draw to the display. 
# A separate thread is used to make inherently synchronous 
# GPIO operations run in parallel with co-operative async operations 
async def _start(): 
    loop = asyncio.get_event_loop()
    executor_pool = concurrent.futures.ThreadPoolExecutor(max_workers = 3)
    blocking_tasks = [
        loop.run_in_executor(executor_pool, _read_temperature),
        loop.run_in_executor(executor_pool, _set_lamp_colour),
        loop.run_in_executor(executor_pool, _print_temperature)
    ]


# Setup and starting of eternal waiting.  
async def main(): 
    IO.setwarnings(False)
    IO.setmode(IO.BOARD)
    IO.setup(11,IO.OUT)
    IO.setup(15,IO.OUT)
    IO.setup(16,IO.OUT)
    IO.setup(18,IO.OUT)
    IO.setup(22,IO.OUT)
    IO.setup(32,IO.OUT)
    IO.setup(36,IO.OUT)
    IO.setup(38,IO.OUT)
    IO.setup(29,IO.OUT)
    IO.setup(31,IO.OUT)
    IO.setup(33,IO.OUT)
    IO.setup(35,IO.OUT)

    await _start() # This is not expected to complete. 


try: 
    loop = asyncio.get_event_loop() 
    loop.run_until_complete(main()) 
except KeyboardInterrupt: 
    for i in range(1,9): 
        # Wipe digit 
        IO.output(segmentsToPins[i],1) 
    for index in range(1,5): 
        IO.output(digitToPins[index], 0) # Disable digit at index 
