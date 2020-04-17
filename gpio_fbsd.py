#
# gpio-fbsd.py
#
# Wrapper around libgpio for FreeBSD.
#
# This library uses ctypes() and its ability to load .so libraries on FreeBSD.
# It simply wraps libgpio.

import ctypes
from ctypes import CDLL,Structure,byref,pointer,c_uint32,c_char,c_char_p
from collections import namedtuple

#
# The following are copied, nearly verbatim, from sys/gpio.h
#

GPIO_PIN_LOW              = 0x00            # low level (logical 0)
GPIO_PIN_HIGH             = 0x01            # high level (logical 1)
GPIO_PIN_INVALID          = 0xdeadbad

GPIOMAXNAME =               64
GPIO_PIN_INPUT =            0x00000001      # input direction
GPIO_PIN_OUTPUT =           0x00000002      # output direction
GPIO_PIN_OPENDRAIN =        0x00000004      # open-drain output
GPIO_PIN_PUSHPULL =         0x00000008      # push-pull output
GPIO_PIN_TRISTATE =         0x00000010      # output disabled
GPIO_PIN_PULLUP =           0x00000020      # internal pull-up enabled
GPIO_PIN_PULLDOWN =         0x00000040      # internal pull-down enabled
GPIO_PIN_INVIN =            0x00000080      # invert input
GPIO_PIN_INVOUT =           0x00000100      # invert output
GPIO_PIN_PULSATE =          0x00000200      # pulsate in hardware
GPIO_PIN_PRESET_LOW =       0x00000400      # preset pin to high or
GPIO_PIN_PRESET_HIGH =      0x00000800      # low before enabling output

# GPIO interrupt capabilities
GPIO_INTR_NONE            = 0x00000000      # no interrupt support
GPIO_INTR_LEVEL_LOW       = 0x00010000      # level trigger, low
GPIO_INTR_LEVEL_HIGH      = 0x00020000      # level trigger, high
GPIO_INTR_EDGE_RISING     = 0x00040000      # edge trigger, rising
GPIO_INTR_EDGE_FALLING    = 0x00080000      # edge trigger, falling
GPIO_INTR_EDGE_BOTH       = 0x00100000      # edge trigger, both
GPIO_INTR_MASK            = (GPIO_INTR_LEVEL_LOW | GPIO_INTR_LEVEL_HIGH | \
                             GPIO_INTR_EDGE_RISING |                      \
                             GPIO_INTR_EDGE_FALLING | GPIO_INTR_EDGE_BOTH)

# Define some types based on ctypes.
gpio_pin_t = c_uint32

class GpioError(Exception):
    """Base class for exceptions in the gpio_fbsd module."""
    pass

class GpioValueError(GpioError):
    """
    Exception raised for errors in pin values.
    Values must be either 0 (GPIO_PIN_LOW) or 1 (GPIO_PIN_HIGH).
    """
    def __init__ (self, bad_value):
        self.value = bad_value
        self.message = "gpio_fbsd: bad pin value {0}".format (bad_value)

class GpioPinNotFoundError(GpioError):
    """
    Exception for "pin not found" errors.
    This can either be because the number is out of range, or because
    the name doesn't exist.
    """
    def __init__ (self, bad_pin_id, max_pin):
        self.pin_id = bad_pin_id
        if type(bad_pin_id) == int:
            self.message = "gpio_fbsd: bad pin number {0}, must be in range 0-{1}".format (bad_pin_id, max_pin)
        elif type(bad_pin_id) == str:
            self.message = "gpio_fbsd: pin name {0} not found".format (bad_pin_id)
        else:
            self.message = "gpio_fbsd: pin identifier must be a number 0-{0} or a pin name".format (max_pin)

class GpioExecutionError (GpioError):
    """
    This error is raised when the GPIO library call fails for some reason.
    """
    def __init__ (self, message):
        self.message = "gpio_fbsd error: {0}".format (message)


class GpioName(Structure):
    _fields_ = [("name", c_char * GPIOMAXNAME)]

GpioConfig = namedtuple ('GpioConfig', ('pin', 'name', 'caps', 'flags'))

class GpioConfigRaw (Structure):
    _fields_ = [("pin", gpio_pin_t),
                ("name", GpioName),
                ("caps", c_uint32),
                ("flags", c_uint32)
               ]

    def get (self):
        return GpioConfig (self.pin, str(self.name, 'UTF-8').rstrip ('\0'), self.caps, self.flags)


GpioConfigPtr = ctypes.POINTER(GpioConfigRaw)

# Load libpio
gpiolib = CDLL("libgpio.so")

class GpioController:
    def __init__ (self, device):
        self.device = device
        self.handle = -1
        if type(device) == int:
            self.handle = gpiolib.gpio_open (device)
        elif type(device) == str:
            self.handle = gpiolib.gpio_open_device (c_char_p (bytes(device, "UTF-8")))
        if self.handle < 0:
            raise GpioExecutionError ("couldn't open GPIO controller {0}".format (device))

        # Initialize the array of pin descriptions. This is only done *once*, with
        # subsequent changes done by either explicitly changing the dicts as needed,
        # or (for reload) by fetching each pin description separately.
        # Calling gpio_pin_list allocates memory that can't be freed, so don't do it
        # more times than needed.
        self.pin_array_raw = GpioConfigPtr ()
        self.max_pin = gpiolib.gpio_pin_list (self.handle, byref(self.pin_array_raw))
        # pins maps pin numbers to configurations
        self.pins = list()
        # names maps pin names to numbers. No need to go the other way, since pin config includes
        # the name.
        self.names = dict()
        for i in range (self.max_pin + 1):
            pin_config = self.pin_array_raw[i].get ()
            self.pins.append (GpioConfig(pin=pin_config.pin, name=pin_config.name,
                                         caps=pin_config.caps, flags=pin_config.flags))
            self.names[pin_config.name] = i

    def pin_num (self, pin):
        if type(pin) == int:
            if 0 <= pin <= self.max_pin:
                return pin
            else:
                raise GpioPinNotFoundError (pin, self.max_pin)
        try:
            return self.names[pin]
        except:
            raise GpioPinNotFoundError (pin, self.max_pin)

    def update_config (self, pin_config):
        try:
            del self.names[pins[pin_config.pin]]
        except:
            pass
        self.names[pin_config.name] = pin_config.pin
        self.pins[pin_config.pin] = pin_config

    def update_config_all (self):
        '''
        Refresh configuration from the underlying system for all pins.
        This may need to be done if pin config is changed by a program
        outside the Python script.
        '''
        # Clear names first
        self.names.clear()
        for i in range (self.max_pin + 1):
            self.pin_config (i)
        return self.pin_list ()


    def pin_get (self, pin):
        v = gpiolib.gpio_pin_get (self.handle, self.pin_num (pin))
        return v

    def pin_set (self, pin, value):
        if value != 0 and value != 1:
            pass
        v = gpiolib.gpio_pin_set (self.handle, self.pin_num (pin), value)
        return v

    def pin_toggle (self, pin):
        v = gpiolib.gpio_pin_toggle (self.handle, self.pin_num (pin))
        return v

    def pin_list (self):
        '''
        Return a list of named tuples containing a GpioConfig for each pin.
        The list is a copy of the internal list. To force a resync with the
        list in the kernel, use update_config_all ().
        '''
        return self.pins[:]

    def pin_config (self, pin):
        '''
        Retrieve the pin configuration for the pin whose ID or name is passed.
        Return value is a GpioConfig namedtuple: (pin, name, caps, flags)
        Also, update the pins and names arrays if needed to reflect the
        newly-retrieved values.
        '''
        pconf_raw = GpioConfigRaw (pin=self.pin_num(pin))
        if gpiolib.gpio_pin_config (self.handle, pointer(pconf_raw)) < 0:
            raise GpioExecutionError ("gio_pin_config (pin={0}) failed".format (self.pin_num (pin)))
        pconf = pconf_raw.get ()
        self.update_config (pconf)
        return pconf

    def pin_set_name (self, pin, name):
        '''
        Set the name for the pin whose ID or (current) name is passed.
        '''
        if name in self.names:
            raise GpioExecutionError ("pin name '{0}' already exists (pin {1})".format (name, self.names[name]))
        pn = self.pin_num (pin)
        if gpiolib.gpio_pin_set_name (self.handle, pn, c_char_p (bytes(name, "UTF-8"))) < 0:
            raise GpioExecutionError ("gpio_pin_set_name (pin={0}, name='{1}') failed".format (pn, name))
        # Delete old name
        del self.names[self.pins[pn].name]
        # Add new name as alias
        self.names[name] = pn
        # Update config
        self.pins[pn] = self.pins[pn]._replace (name=name)
        return v

    def pin_set_flags (self, pin, flags):
        '''
        Set the flags for the pin whose ID or name is passed.
        '''
        pn = self.pin_num (pin)
        pconf_raw = GpioConfigRaw (pin=pn, flags=flags)
        if gpiolib.gpio_pin_set_flags (self.handle, byref(pconf_raw)) < 0:
            raise GpioExecutionError ("gpio_pin_set_flags (pin={0}, flags=0x{1:08x}) failed".format (pn, flags))
        self.pins[pn] = self.pins[pn]._replace (flags=flags)
        return v

    def close (self):
        gpiolib.close (self.handle)

    # Functions below this point are helper functions.
    # We provide access to them because it's simple, and because users may prefer
    # to use them.

    def pin_low (self, pin):
        '''
        Set the state of this pin to low.
        '''
        return gpiolib.gpio_set_pin_low (g.handle, self.pin_num (pin))

    def pin_high (self, pin):
        '''
        Set the state of this pin to high.
        '''
        return gpiolib.gpio_set_pin_high (g.handle, self.pin_num (pin))

    def pin_input (self, pin):
        '''
        Configure this pin to be an input pin. Since this changes the
        configuration, also call pin_config to update internal configuration.
        '''
        pn = self.pin_num (pin)
        ret = gpiolib.gpio_pin_input (g.handle, pn)
        self.pin_config (pn)
        return ret

    def pin_output (self, pin):
        '''
        Configure this pin to be an output pin. Since this changes the
        configuration, also call pin_config to update internal configuration.
        '''
        pn = self.pin_num (pin)
        ret = gpiolib.gpio_pin_output (g.handle, pn)
        self.pin_config (pn)
        return ret

    def pin_opendrain (self, pin):
        '''
        Configure this pin to be an open drain pin. Since this changes the
        configuration, also call pin_config to update internal configuration.
        '''
        pn = self.pin_num (pin)
        ret = gpiolib.gpio_pin_opendrain (g.handle, pn)
        self.pin_config (pn)
        return ret

    def pin_pushpull (self, pin):
        '''
        Configure this pin to be a push-pull pin. Since this changes the
        configuration, also call pin_config to update internal configuration.
        '''
        pn = self.pin_num (pin)
        ret = gpiolib.gpio_pin_pushpull (g.handle, pn)
        self.pin_config (pn)
        return ret

    def pin_tristate (self, pin):
        '''
        Configure this pin to be a tristate pin. Since this changes the
        configuration, also call pin_config to update internal configuration.
        '''
        pn = self.pin_num (pin)
        ret = gpiolib.gpio_pin_tristate (g.handle, pn)
        self.pin_config (pn)
        return ret

    def pin_pullup (self, pin):
        '''
        Configure this pin to be a pullup pin. Since this changes the
        configuration, also call pin_config to update internal configuration.
        '''
        pn = self.pin_num (pin)
        ret = gpiolib.gpio_pin_pullup (g.handle, pn)
        self.pin_config (pn)
        return ret

    def pin_pulldown (self, pin):
        '''
        Configure this pin to be an pulldown pin. Since this changes the
        configuration, also call pin_config to update internal configuration.
        '''
        pn = self.pin_num (pin)
        ret = gpiolib.gpio_pin_pulldown (g.handle, pn)
        self.pin_config (pn)
        return ret

    def pin_invin (self, pin):
        '''
        Configure this pin to be an inverted input pin. Since this changes the
        configuration, also call pin_config to update internal configuration.
        '''
        pn = self.pin_num (pin)
        ret = gpiolib.gpio_pin_invin (g.handle, pn)
        self.pin_config (pn)
        return ret

    def pin_invout (self, pin):
        '''
        Configure this pin to be an inverted output pin. Since this changes the
        configuration, also call pin_config to update internal configuration.
        '''
        pn = self.pin_num (pin)
        ret = gpiolib.gpio_pin_invout (g.handle, pn)
        self.pin_config (pn)
        return ret

    def pin_pulsate (self, pin):
        '''
        Configure this pin to be a pulsate pin. Since this changes the
        configuration, also call pin_config to update internal configuration.
        '''
        pn = self.pin_num (pin)
        ret = gpiolib.gpio_pin_pulsate (g.handle, pn)
        self.pin_config (pn)
        return ret


if __name__ == '__main__':
    pass
