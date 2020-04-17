#
# gpio-fbsd.py
#
# Wrapper around libgpio for FreeBSD.
#
# This library uses ctypes() and its ability to load .so libraries on FreeBSD.
# It simply wraps libgpio.

import ctypes
from ctypes import CDLL,Structure

GPIOMAXNAME = 64                    # from <sys/gpio.h>
gpio_uint32_t = ctypes.c_uint       # 32-bit unsigned integer
gpio_pin_t    = ctypes.c_uint
gpio_char_t = ctypes.c_char



class GpioName(Structure):
    _fields_ = [("name", gpio_char_t * GPIOMAXNAME)]

class GpioConfig (Structure):
    _fields_ = [("pin", gpio_pin_t),
                ("name", GpioName),
                ("caps", gpio_uint32_t),
                ("flags", gpio_uint32_t)
               ]

class GpioController:
    def __init__ (self, device):
        self.gpiolib = CDLL("libgpio.so")
        self.device = device
        if type(device) == type(0):
            self.handle = self.gpiolib.gpio_open (device)
        elif type(device) == type ("x"):
            self.handle = self.gpiolib.gpio_open_device (device)


    def pin_get (self, pin):
        v = self.gpiolib.gpio_pin_get (self.handle, pin)
        return v

    def pin_set (self, pin, value):
        v = self.gpiolib.gpio_pin_set (self.handle, pin, value)
        return v

    def pin_toggle (self, pin):
        v = self.gpiolib.gpio_pin_toggle (self.handle, pin)
        return v

    def close (self):
        gpiolib.close (self.handle)

if __name__ == '__main__':
    pass
