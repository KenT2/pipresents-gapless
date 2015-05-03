"""
!!!! THIS PROGRAM COULD DAMAGE YOUR PI IF GPIO IS NOT CORRECTLY CONNECTED
To Run - sudo python output_test.py from a terminal window
All outputs that can be used by Pi Presents will change state every 5 seconds
A log will be written to the terminal window.
To exit type CTRL-C
 
"""

import RPi.GPIO as GPIO
from time import sleep


def write_pins(value):
    for pin in pins:
        print 'Pin ',pin,value
        GPIO.output(pin,value)


ON_VALUE= GPIO.HIGH
OFF_VALUE=GPIO.LOW

pins=[3,5,7,8,10,11,12,13,15,16,18,19, 21, 22, 23, 24, 26]

# b+ etc. pins=[3,5,7,8,10,11,12,13,15,16,18,19, 21, 22, 23, 24, 26,29,31,32,33,35,36,37,38,40]

GPIO.setwarnings(False)
GPIO.cleanup()

GPIO.setmode(GPIO.BOARD)

for pin in pins:
    GPIO.setup(pin,GPIO.OUT)

while True:
        print '\n***** ON ******'
        write_pins(ON_VALUE)
        sleep (5)
        print '\n***** OFF *****'
        write_pins(OFF_VALUE)
        sleep(5)



