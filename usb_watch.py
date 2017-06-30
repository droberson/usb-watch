#!/usr/bin/env python

"""
usb_watch.py -- watch for USB events and make notify of them

STILL REALLY ROUGH. 6/26/2017 Daniel Roberson @dmfroberson

Requires:
  - pyudev


TODO:
 - Meaningful docstrings
 - General cleanup
 - Vendor and product lookups
 - argparse: toggle SMS
 - syslog?
"""

import os
import socket
import glib
from twilio.rest import Client
import settings as twilio_settings
from pyudev import Context, Monitor


try:
    from pyudev.glib import MonitorObserver

    def device_event(observer, device):
        """
        docstring
        """
        getsome(device, device.action)

except ImportError:
    from pyudev.glib import GUDevMonitorObserver as MonitorObserver

    def device_event(observer, action, device):
        """
        docstring
        """
        getsome(device, action)


# Globals
USB_DEVICES = []


def send_sms(message):
    """
    docstring
    TODO: add error checking, perhaps move client to global so it doesn't
          have to be created every time (or destroy it). RTFM.
    """
    client = Client(twilio_settings.account_sid, twilio_settings.auth_token)

    message = client.api.account.messages.create(to=twilio_settings.phone_to,
                                                 from_=twilio_settings.phone_from,
                                                 body=message)
    return True


def get_device_info(device, item):
    """
    docstring
    """
    device_info = device.sys_path + "/" + item

    if os.path.isfile(device_info) is True:
        with open(device_info) as usb_device:
            for line in usb_device:
                return line.rstrip(os.linesep)

    return None


def getsome(device, action):
    """
    docstring
    """
    if action == "add":
        busnum = get_device_info(device, "busnum")
        devnum = get_device_info(device, "devnum")
        id_product = get_device_info(device, "idProduct")
        id_vendor = get_device_info(device, "idVendor")
        manufacturer = get_device_info(device, "manufacturer")
        product = get_device_info(device, "product")

        if busnum:
            USB_DEVICES.append((device.device_path,
                                busnum,
                                devnum,
                                id_vendor,
                                id_product,
                                manufacturer,
                                product))
            print "Add -- %s Bus: %s Device: %s %s:%s %s %s" % \
                (device.device_path, busnum, devnum, id_vendor, id_product,
                 manufacturer, product)
            send_sms("%s USB add: %s:%s, %s:%s %s %s" % \
                     (socket.gethostname(), busnum, devnum, id_vendor,
                      id_product, manufacturer, product))

    if action == "remove":
        result = next((i for i, v in enumerate(USB_DEVICES) \
                       if v[0] == device.device_path), None)
        if result:
            busnum = USB_DEVICES[result][1]
            devnum = USB_DEVICES[result][2]
            id_vendor = USB_DEVICES[result][3]
            id_product = USB_DEVICES[result][4]
            manufacturer = USB_DEVICES[result][5]
            product = USB_DEVICES[result][6]

            print "Remove -- %s Bus: %s Device: %s %s:%s %s %s" % \
                (device.device_path, busnum, devnum, id_vendor, id_product,
                 manufacturer, product)
            send_sms("%s USB remove: %s:%s, %s:%s %s %s" % \
                     (socket.gethostname(), busnum, devnum, id_vendor,
                      id_product, manufacturer, product))

            USB_DEVICES.pop(result)


def main():
    """
    docstring
    """
    context = Context()

    # Populate list of current USB devices
    for device in context.list_devices(subsystem="usb"):
        busnum = get_device_info(device, "busnum")
        devnum = get_device_info(device, "devnum")
        id_product = get_device_info(device, "idProduct")
        id_vendor = get_device_info(device, "idVendor")
        manufacturer = get_device_info(device, "manufacturer")
        product = get_device_info(device, "product")

        if busnum:
            USB_DEVICES.append((device.device_path,
                                busnum,
                                devnum,
                                id_vendor,
                                id_product,
                                manufacturer,
                                product))

    monitor = Monitor.from_netlink(context)

    monitor.filter_by(subsystem='usb')
    observer = MonitorObserver(monitor)

    observer.connect('device-event', device_event)
    monitor.start()

    print "[+] usb-watch by Daniel Roberson @dmfroberson Started."

    glib.MainLoop().run()


if __name__ == "__main__":
    main()
