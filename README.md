# Overview

`python-GPIOfbsd` is a Python module that allows users to access the GPIO pins
on a Raspberry Pi through the `libgpio` library on FreeBSD 12. Unlike some
other modules, `python-GPIOfbsd` requires _no_ C compilation of any kind.
It doesn't use `cffi`, and requires no additional downloads. This may make it
easier to get working in the first place, and easier to maintain.

## Requirements

There are no requirements beyond Python 3. The module is a single Python 3
`.py` file which can be imported into any Python program.

## Status

The code has been tested on FreeBSD 12.1 using Python 3.7. It's pretty vanilla
Python, so it should work fine on any Python 3.X.

The code _requires_ `libgpio`, which may only be present on certain versions
of FreeBSD. It also requires a working `ctypes` library module in Python;
however, since that's part of the basic distribution, it shouldn't require
additional downloads.

## Installation

Install the code by placing `GPIOfbsd.py` anywhere that your program can find it to
load. There are no complex paths in the module, and the only library modules that
are used are `ctypes` and `collections`, both of which are a core part of every Python
3 distribution.

# Usage

## Accessing the GPIO device

First, make sure that the user you're running as has read/write access to the GPIO
device you want to use. This is often not the case with FreeBSD on Raspberry PI,
which makes the GPIO device (typically `/dev/gpioc0`) read-only. Your options are
to either change the permissions on the device file using `chmod`, or to run as
the user who _does_ have access. I recommend the former approach. If you're concerned
about making the device globally read/write, you can create a `gpiousers` group,
add members of `wheel` (`root` and `freebsd`) to the new group, and then add your
own user ID to `gpiousers` as well.
You'll still have to switch effective groups using `newgrp`, but that may not be as
bad as opening up the GPIO pins.

## Importing the module

Import the module as you usually would with any Python module:

`
    import GPIOfbsd
`

The module defines a lot of GPIO constants (taken from `/usr/include/sys/gpio.h`), all of
which start with `GPIO_`. Classes all start with Gpio.

## Using the module

First, create a controller instance:

`
    controller = GpioController (0)
`

The value passed to `GpioController` can be either the GPIO device number, or the actual name of the device
(on my system, it's `/dev/gpioc0`). If the GPIO controller can't be opened, an exception is thrown.

Now, you can use `controller` to read and write information about the GPIO device. For example:

`
    pins = controller.pin_list ()        # Returns a list of GpioConfig descriptions of all of the pins
    pin8 = controller.pin_config (8)     # Returns the GpioConfig for pin 8
    pin7 = controller.pin_config ('pin 7') # All pin-based functions take either the pin number or pin name
    controller.pin_set (8, 1)            # Set pin 8 to output value 1
    controller.pin_get (8)               # Get the current value of pin 8
`

The rules that apply to GPIO devices still apply here. For example, if pin 4 is an input pin, setting its value
has no effect, and won't cause an error because `libgpio` doesn't return an error.

`GPIOfbsd` supports all of the functions described in [`gpio(3)`](https://www.freebsd.org/cgi/man.cgi?gpio),
without the leading `gpio_` prefix. All pin-based functions take either a pin number or a pin name, and throw
a `GpioValueException` if the pin doesn't exist.

Arguments to the `gpio_` functions are the same as listed on [`gpio(3)`](https://www.freebsd.org/cgi/man.cgi?gpio),
without the handle, which is supplied by the controller object. The following functions take different arguments
in the controller version:

*  `pin_list`: takes no arguments, returns a list of `GpioConfig` `namedtuple`s
*  `pin_config`: takes the pin name/number as an argument, returns a single `GpioConfig` `namedtuple`
*  `pin_set_flags`: takes the pin name/number and the flags to which the pin is to be set

The controller automatically closes the GPIO device when it's deleted (or goes out of scope). The `close` method
is available if desired, but there's no need for the user to call it.

## Further information on GPIO

Look at the [man page for `gpio(3)`](https://www.freebsd.org/cgi/man.cgi?gpio)
on FreeBSD for a description of what the `gpio_XXX` calls do. This module
implements all of them.

# Author

The code and documentation is (c) 2020 by Ethan L. Miller (`coding<at>ethanmiller.org`).
It's released under the BSD 3-clause license.
