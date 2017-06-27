#!/usr/bin/env python

"""
usb_watch.py -- watch for USB events and make notify of them

STILL REALLY ROUGH. 6/26/2017 Daniel Roberson @dmfroberson

Requires:
  - pyudev


TODO:
 - Meaningful docstrings
 - General cleanup
 - Popuate list of current USB devices at startup
 - Twilio API to SMS on events.
 - Vendor and product lookups 
"""

import os
#import sys
import glib
import usb.core
from pyudev import Context, Monitor


try:
    from pyudev.glib import MonitorObserver

    def device_event(observer, device):
        """
        docstring
        """
        getsome(device, device.action)

except:
    from pyudev.glib import GUDevMonitorObserver as MonitorObserver

    def device_event(observer, action, device):
        """
        docstring
        """
        getsome(device, action)


def get_device_info(device, item):
    """
    docstring
    """
    device_info = "/sys" + device.device_path + "/" + item
    if os.path.isfile(device_info) is True:
        with open(device_info) as f:
            for line in f:
                return line.rstrip(os.linesep)
    return None


def getsome(device, action):
    """
    docstring
    """
    busnum = None
    devnum = None
    idProduct = None
    idVendor = None

    if action == "add":
        busnum = get_device_info(device, "busnum")
        devnum = get_device_info(device, "devnum")
        idProduct = get_device_info(device, "idProduct")
        idVendor = get_device_info(device, "idVendor")

        if busnum:
            print "Add -- %s Bus: %s Device: %s %s:%s" % \
                (device.device_path, busnum, devnum, idVendor, idProduct)

    if action == "remove":
        # TODO: this doesn't work. lookup device from pre-populated table
        busnum = get_device_info(device, "busnum")
        devnum = get_device_info(device, "devnum")
        idProduct = get_device_info(device, "idProduct")
        idVendor = get_device_info(device, "idVendor")

        print "Remove -- %s Bus: %s Device: %s %s:%s" % \
            (device.device_path, busnum, devnum, idVendor, idProduct)


def main():
    """
    docstring
    """

    # TODO: save this information for use with "remove" action.
    dev = usb.core.find(find_all=True)
    for cfg in dev:
        print "Bus: %s Device: %s" % (cfg.bus, cfg.address)
        print "VendorID: %s ProductID: %s" % \
            (hex(cfg.idVendor), hex(cfg.idProduct))

    context = Context()
    monitor = Monitor.from_netlink(context)

    monitor.filter_by(subsystem='usb')
    observer = MonitorObserver(monitor)

    observer.connect('device-event', device_event)
    monitor.start()

    glib.MainLoop().run()


if __name__ == "__main__":
    main()
