#
#
# Test harness for GPIOfbsd.py
#
# This is set up as a separate file so that it doesn't need to be imported
# with the main code. Also, it ensures that functionality is available
# when the module is imported.
#
#############################################################################
#
# BSD 3-Clause License
#
# Copyright (c) 2020, Ethan L. Miller
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import re, sys
import unittest
from subprocess import run
import GPIOfbsd as g

# This must be set to the name of the GPIO controller you want to use.
# Typically, this is /dev/gpioc0 on a Raspberry Pi.
# The device must be readable and writable by the Python script.
controller_name = "/dev/gpioc0"

###########################################################################
# No need to modify below here.
###########################################################################

gpioctl_flags = {
    'IN'     : g.GPIO_PIN_INPUT,
    'OUT'    : g.GPIO_PIN_OUTPUT,
    'PU'     : g.GPIO_PIN_PULLUP,
    'PD'     : g.GPIO_PIN_PULLDOWN,
}

def setUpModule ():
    global controller
    controller = g.GpioController (controller_name)

def tearDownModule ():
    controller.close ()

def pin_value_from_cmd (ctrl, pin):
    result = run (['gpioctl', '-f', ctrl, str(pin)], capture_output=True, encoding="UTF-8", check=True)
    return int(result.stdout)

def make_config_from_match (m):
    flags = 0
    caps = 0
    flag_list = m['flags'].split (',')
    cap_list = m['caps'].split(',')
    for k,v in gpioctl_flags.items():
        if k in flag_list:
            flags |= v
        if k in cap_list:
            caps |= v
    return g.GpioConfig (pin=int(m['pin']), name=m['name'], caps=caps, flags=flags)

def pin_config_from_cmd (ctrl, pin = None):
    result = run (['gpioctl', '-f', ctrl,'-l', '-v'],
                  capture_output=True, encoding="UTF-8", check=True)
    configs = result.stdout.split ('\n')
    config_pat = re.compile (r'^pin (?P<pin>\d+):\s+(?P<value>\d)\s+(?P<name>.*)\<(?P<flags>IN|OUT|PU|PD|)\>,\s*caps:\<(?P<caps>[A-Z,]+)\>')
    if pin != None:
        for c in configs:
            m = config_pat.search (c)
            if m and int(m['pin']) == pin:
                return make_config_from_match (m)
    else:
        config_list = []
        for c in configs:
            m = config_pat.search (c)
            if m:
                config_list.append (make_config_from_match (m))
        return config_list
    return None

class TestGpioControllerConfigMethods (unittest.TestCase):
    def test_pinlist(self):
        pin_list = controller.pin_list ()
        for p in pin_list:
            by_pin = controller.pin_config (p.pin)
            by_name = controller.pin_config (p.name)
            assert (p == by_pin)
            assert (p == by_name)

    def test_pinconfig (self):
        for p in controller.pin_list ():
            cnf_py = controller.pin_config (p.pin)
            cnf_py = cnf_py._replace (caps = cnf_py.caps & ~g.GPIO_INTR_MASK)
            cnf_un = pin_config_from_cmd (controller_name, p.pin)
            assert cnf_py == cnf_un

class TestGpioControllerPinMethods (unittest.TestCase):
    def test_pin_get (self):
        for p in controller.pin_list ():
            if not (p.flags & g.GPIO_PIN_OUTPUT):
                continue
            v_py = controller.pin_get (p.pin)
            v_un = pin_value_from_cmd (controller_name, p.pin)
            assert v_py == v_un

    def test_pin_set (self):
        for p in controller.pin_list ():
            if not (p.flags & g.GPIO_PIN_OUTPUT):
                continue
            orig_v = controller.pin_get (p.pin)
            other_v = 1 - orig_v
            controller.pin_set (p.pin, other_v)
            assert controller.pin_get (p.pin) == other_v
            controller.pin_set (p.name, orig_v)
            assert controller.pin_get (p.pin) == orig_v

    def test_pin_toggle (self):
        for p in controller.pin_list ():
            if not (p.flags & g.GPIO_PIN_OUTPUT):
                continue
            orig_v = controller.pin_get (p.pin)
            controller.pin_toggle (p.pin)
            assert controller.pin_get (p.pin) == 1 - orig_v
            controller.pin_toggle (p.name)
            assert controller.pin_get (p.pin) == orig_v

if __name__ == '__main__':
    unittest.main ()
