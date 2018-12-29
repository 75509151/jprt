#!/bin/sh
ps aux |grep -E "kiosk_init" |grep -v grep > /dev/null
if [ "$?" -eq 0 ]
    then 
        echo "already run one"
else
    echo "run cereson services which want run on power on and doesn't need net(because net maybe doesn't init)"
    /home/mm/.pyenv/shims/python /home/mm/kiosk/src/shell/kiosk_init.pyc
    chown -R pi:pi /home/mm/var/data/db/
    chown -R pi:pi /home/mm/var/log/
    
fi

