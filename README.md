# usb-watch
Use Python pyudev to monitor for USB events. Sends SMS texts via Twilio if
something is plugged in/removed from the machine.

## Quickstart

- This has only been tested on Linux!!

- This depends on the pyudev and twilio Python modules. Install them
  using your distro's package system or pip.

- Go to Twilio.com and sign up. You will need your SID, auth token, and a 
  phone number.

- Place these settings into settings.py (you will need to create this file)
  using example_settings.py as a template.
  
- Run it: ./usb_watch.py
