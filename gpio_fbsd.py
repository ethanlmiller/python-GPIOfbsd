#
# gpio-fbsd.py
#
# Wrapper around libgpio for FreeBSD.
#
# This library uses ctypes() and its ability to load .so libraries on FreeBSD.
# It simply wraps libgpio.

import ctypes
from ctypes import CDLL,Structure,byref
from collections import namedtuple

GPIOMAXNAME = 64                    # from <sys/gpio.h>
gpio_uint32_t = ctypes.c_uint       # 32-bit unsigned integer
gpio_pin_t    = ctypes.c_uint
gpio_char_t = ctypes.c_char



class GpioName(Structure):
    _fields_ = [("name", gpio_char_t * GPIOMAXNAME)]

GpioConfig = namedtuple ('GpioConfig', ('pin', 'name', 'caps', 'flags'))

class GpioConfigRaw (Structure):
    _fields_ = [("pin", gpio_pin_t),
                ("name", GpioName),
                ("caps", gpio_uint32_t),
                ("flags", gpio_uint32_t)
               ]
    def get (self):
        return GpioConfig (self.pin, str(self.name, 'UTF-8').rstrip ('\0'), self.caps, self.flags)


GpioConfigPtr = ctypes.POINTER(GpioConfigRaw)

class GpioController:
    def __init__ (self, device):
        self.gpiolib = CDLL("libgpio.so")
        self.device = device
        if type(device) == type(0):
            self.handle = self.gpiolib.gpio_open (device)
        elif type(device) == type ("x"):
            self.handle = self.gpiolib.gpio_open_device (device)
        # Initialize the array of pin descriptions. This is only done *once*, with
        # subsequent changes done by either explicitly changing the dicts as needed,
        # or (for reload) by fetching each pin description separately.
        # Calling gpio_pin_list allocates memory that can't be freed, so don't do it
        # more times than needed.
        self.pin_array_raw = GpioConfigPtr ()
        self.max_pin = self.gpiolib.gpio_pin_list (self.handle, byref(self.pin_array_raw))
        # pins maps pin numbers to configurations
        self.pins = list()
        # names maps pin names to numbers. No need to go the other way, since pin config includes
        # the name.
        self.names = dict()
        for i in range (self.max_pin + 1):
            pin_config = self.pin_array_raw[i].get ()
            self.pins.append ((pin_config.pin, pin_config.name, pin_config.caps, pin_config.flags))
            self.names[pin_config.name] = i

    def pin_num_from_id (self, pin):
        if type(pin) == type(0):
            return pin
        try:
            return self.names[pin]
        except:
            pass

    def update_config (self, pin_config):
        try:
            del names[pins[pin_config.pin]]
        except:
            pass
        names[pin_config.name] = pin_config.pin
        pins[pin_config.pin] = pin_config

    def pin_get (self, pin):
        v = self.gpiolib.gpio_pin_get (self.handle, pin)
        return v

    def pin_set (self, pin, value):
        v = self.gpiolib.gpio_pin_set (self.handle, pin, value)
        return v

    def pin_toggle (self, pin):
        v = self.gpiolib.gpio_pin_toggle (self.handle, pin)
        return v

    def pin_list (self):
        return self.pins[:]

    def pin_config (self, pin):
        '''
        Retrieve the pin configuration for the pin whose ID or name is passed.
        Return value is a GpioConfig namedtuple: (pin, name, caps, flags)
        Also, update the pins and names arrays if needed to reflect the
        newly-retrieved values.
        '''
        pconf_raw = GpioConfigPtr ()
        v = self.gpiolib.gpio_pin_config (self.handle, pconf_raw)
        pconf = pconf_raw.get ()
        self.update_config (pconf)
        return pconf

    def pin_set_name (self, pin, name):
        '''
        Set the name for the pin whose ID or (current) name is passed.
        '''
        pass

    def pin_set_flags (self, pin, flags):
        '''
        Set the flags for the pin whose ID or name is passed.
        '''
        pass

    def close (self):
        gpiolib.close (self.handle)

if __name__ == '__main__':
    pass
