#!/usr/bin/env python

"""
usb_watch.py -- watch for USB events and make notify of them

STILL REALLY ROUGH. 6/26/2017 Daniel Roberson @dmfroberson

Requires:
  - pyudev


TODO:
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
        """ device_event() -- glue function for udev device handler
        """
        event_handler(device, device.action)

except ImportError:
    from pyudev.glib import GUDevMonitorObserver as MonitorObserver

    def device_event(observer, action, device):
        """ device_event() -- glue function for udev device handler
        """
        event_handler(device, action)


# Globals
USB_DEVICES = []


def send_sms(message):
    """ send_sms() -- Sends an SMS message using Twilio

    Args:
        message (str) - The message to send

    Returns:
        True.

    TODO: add error checking, perhaps move client to global so it doesn't
          have to be created every time (or destroy it). RTFM.
    """
    client = Client(twilio_settings.account_sid, twilio_settings.auth_token)

    message = client.api.account.messages.create(to=twilio_settings.phone_to,
                                                 from_=twilio_settings.phone_from,
                                                 body=message)
    return True


def get_device_info(device, item):
    """ get_device_info() -- retrieve information about a USB device

    Args:
        device (pyudev device object) - Udev device to retrieve information from
        item (str)                    - Which item to retrieve

    Returns:
        str: The contents of "item". Otherwise, None.
    """
    device_info = device.sys_path + "/" + item

    if os.path.isfile(device_info) is True:
        with open(device_info) as usb_device:
            for line in usb_device:
                return line.rstrip(os.linesep)

    return None


def event_handler(device, action):
    """ event_handler() -- Handles udev events

    Args:
        device (pyudev device object) - Device on which an event has occurred.
        action (str)                  - Which event: add or remove

    Returns:
        Nothing.
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

    elif action == "remove":
        result = next((i for i, v in enumerate(USB_DEVICES) \
                       if v[0] == device.device_path), None)
        if result:
            busnum = USB_DEVICES[result][1]
            devnum = USB_DEVICES[result][2]
            id_vendor = USB_DEVICES[result][3]
            id_product = USB_DEVICES[result][4]
            manufacturer = USB_DEVICES[result][5]
            product = USB_DEVICES[result][6]

            print "[+] Remove -- %s Bus: %s Device: %s %s:%s %s %s" % \
                (device.device_path, busnum, devnum, id_vendor, id_product,
                 manufacturer, product)
            send_sms("%s USB remove: %s:%s, %s:%s %s %s" % \
                     (socket.gethostname(), busnum, devnum, id_vendor,
                      id_product, manufacturer, product))

            USB_DEVICES.pop(result)

    else:
        print "[-] Unknown event: %s" % action


def main():
    """ main() -- entry point for this program
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
