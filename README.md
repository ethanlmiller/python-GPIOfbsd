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
which start with `GPIO_`. Beyond that, 

But look at the [man page for `gpio(3)`](https://www.freebsd.org/cgi/man.cgi?gpio)
on FreeBSD for a description of what the `gpio_XXX` calls do. This module
implements all of them.

# Author

The code and documentation is (c) 2020 by Ethan L. Miller (`coding<at>ethanmiller.org`).
It's released under the BSD 3-clause license.
