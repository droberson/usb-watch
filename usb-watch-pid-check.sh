#!/bin/sh

#
# usb-watch-pid-check.sh -- by Daniel Roberson
# -- simple script to respawn usb-watch if it dies.
# -- meant to be placed in your crontab!
# --
# -- * * * * * /path/to/usb-watch-pid-check.sh
#

# Season to taste:
PIDFILE="/home/user/usb-watch.pid"
BINPATH="/home/user/usb-watch/usb-watch.py -d -p $PIDFILE"

if [ ! -f $PIDFILE ]; then
    # PIDFILE doesnt exist!
    echo "usb-watch not running. Attempting to start"
    $BINPATH
    exit
else
    # PID file exists. check if its running!
    kill -0 "$(head -n 1 $PIDFILE)" 2>/dev/null
    if [ $? -eq 0 ]; then
        exit 0
    else
        echo "usb-watch not running. Attempting to start.."
        $BINPATH
    fi
fi
