"""
To Run - sudo python input_test.py from a terminal window
All inputs that can be used by Pi Presents will be read every second and printed to the terminal
To exit type CTRL-C
"""

import RPi.GPIO as GPIO
from time import sleep


def read_pins():
    print ""
    for pin in pins:
        print "Pin ",pin,GPIO.input(pin)
            

pins=[3,5,7,8,10,11,12,13,15,16,18,19, 21, 22, 23, 24, 26]
# b+ etc. pins=[3,5,7,8,10,11,12,13,15,16,18,19, 21, 22, 23, 24, 26,29,31,32,33,35,36,37,38,40]

# pins 3 and 5 have permanent 1.8k pull ups to 3.3 volts and will therefore be 1 even if PULL_UP=GPIO.PUD_DOWN
# comment out all but the internal pullup value you want
PULL=GPIO.PUD_UP            # internal pullup resistor to 3.3 volts
#PULL=GPIO.PUD_DOWN   #internal pullup resistor to 0 volts
#PULL=GPIO.PUD_OFF        # internal pullup resistor disconnected

GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)
for pin in pins:
    GPIO.setup(pin,GPIO.IN,pull_up_down=PULL)
while True:
    read_pins()
    sleep (1)



