#!/usr/bin/env python

"""
usb_watch.py -- Watch for USB events on a Linux machine.

Not as rough, but still not 100% 6/30/2017 Daniel Roberson @dmfroberson

Requires:
  - pyudev
"""

import argparse
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
SEND_SMS = True
DAEMONIZE = False
PID_FILE = "usb-watch.pid"


def xprint(buf):
    """ xprint() -- wrapper for print. Quiet if daemonized. Logs if enabled.

    Args:
        buf (str) - String to output

    Returns:
        Nothing.

    TODO:
     - add logging
    """
    if DAEMONIZE:
        return

    print buf


def send_sms(message):
    """ send_sms() -- Sends an SMS message using Twilio

    Args:
        message (str) - The message to send

    Returns:
        True if message is sent
        False if message is not sent

    TODO: add error checking, perhaps move client to global so it doesn't
          have to be created every time (or destroy it). RTFM.
    """
    if not SEND_SMS:
        return False

    client = Client(twilio_settings.account_sid, twilio_settings.auth_token)

    message = client.api.account.messages.create(
        to=twilio_settings.phone_to,
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
            xprint("[+] Add -- %s Bus: %s Device: %s %s:%s %s %s" % \
                (device.device_path, busnum, devnum, id_vendor, id_product,
                 manufacturer, product))
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

            xprint("[+] Remove -- %s Bus: %s Device: %s %s:%s %s %s" % \
                (device.device_path, busnum, devnum, id_vendor, id_product,
                 manufacturer, product))
            send_sms("%s USB remove: %s:%s, %s:%s %s %s" % \
                     (socket.gethostname(), busnum, devnum, id_vendor,
                      id_product, manufacturer, product))

            USB_DEVICES.pop(result)

    else:
        xprint("[-] Unknown event: %s" % action)


def write_pid_file(pid_file, pid):
    """ write_pid_file() -- writes a PID file

    Args:
        pid_file (str) - PID file to write to
        pid (int)      - PID

    Returns:
        Nothing. Exits on failure.
    """
    try:
        with open(pid_file, "w") as outfile:
            outfile.write(str(pid))

    except IOError as err:
        xprint("[-] Unable to open PID file %s for writing: %s" % \
            (pid_file, err))
        xprint("[-] Exiting.")
        exit(os.EX_USAGE)


def parse_cli():
    """ parse_cli() -- parses CLI input

    Args:
        None

    Returns:
        ArgumentParser namespace relevant to supplied CLI options
    """
    description = "example: ./usb-watch.py [-d] [-p <pid file>] [-s]"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("-p",
                        "--pid_file",
                        help="Location of PID file",
                        default=PID_FILE,
                        required=False)
    parser.add_argument("-d",
                        "--daemonize",
                        help="Daemonize/fork to background",
                        action="store_true")
    parser.add_argument("-s",
                        "--sms",
                        help="Disable SMS messaging",
                        action="store_false")

    args = parser.parse_args()
    return args


def main():
    """ main() -- entry point for this program
    """
    global SEND_SMS
    global DAEMONIZE
    global PID_FILE

    # Parse CLI options
    args = parse_cli()

    DAEMONIZE = args.daemonize
    PID_FILE = args.pid_file
    SEND_SMS = args.sms

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

    if DAEMONIZE:
        usbwatch_pid = os.fork()

        if usbwatch_pid != 0:
            return os.EX_OK

    write_pid_file(PID_FILE, os.getpid())

    xprint("[+] usb-watch by Daniel Roberson @dmfroberson Started. PID %s" % \
        os.getpid())

    try:
        glib.MainLoop().run()
    except KeyboardInterrupt:
        print "[-] Caught Control-C. Andross has ordered us to take you down."
        print "[-] Exiting."

    return os.EX_OK


if __name__ == "__main__":
    exit(main())
