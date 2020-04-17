# python-GPIOfbsd

This is a Python-only module that allows users to access the GPIO pins
on a Raspberry Pi through the `libgpio` library on FreeBSD 12.

## Requirements

There are no requirements beyond Python 3. The module is a single Python 3
`.py` file which can be imported into any program.

## Status

The code has been tested on FreeBSD 12.1 using Python 3.7. It's pretty vanilla
Python, so it should work fine on any Python 3.X.

The code _requires_ `libgpio`, which may only be present on certain versions
of FreeBSD. It also requires a working `ctypes` library module in Python;
however, since that's part of the basic distribution, it shouldn't require
additional downloads.

# Documentation

## Installation

Install the code by placing `GPIOfbsd.py` anywhere that your program can find it to
load.

## Usage

TBD

But look at the [man page for `gpio(3)`](https://www.freebsd.org/cgi/man.cgi?gpio)
on FreeBSD for a description of what the `gpio_XXX` calls do. This module
implements all of them.

# Author

The code and documentation is (c) 2020 by Ethan L. Miller (`coding@ethanmiller.org`).
It's released under the BSD 3-clause license.
