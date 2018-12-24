#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2015 HP Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch
#

__version__ = '5.2'
__title__ = 'Device Information Utility'
__mod__ = 'hp-info'
__doc__ = "Query a printer for static model information, dynamic status information, and CUPS printer queue settings."

# Std Lib
import sys
import getopt
import time
import os



# Local
from base.g import *
from base import device, status, utils, tui, module
from prnt import cups

try:
    from importlib import import_module
except ImportError as e:
    log.debug(e)
    from base.utils import dyn_import_mod as import_module


try:

    devid_mode = False
    restrict = True


    mod = module.Module(__mod__, __title__, __version__, __doc__, None,
                        (INTERACTIVE_MODE, GUI_MODE), (UI_TOOLKIT_QT4, UI_TOOLKIT_QT5),
                        False, devid_mode)


    restrict = False

    device_uri = None
    printer_name = None


    device_uri = mod.getDeviceUri(device_uri, printer_name, restrict_to_installed_devices=restrict)

    if not device_uri:
        print("not device_uri")
        log.debug("not device_uri")
        sys.exit(1)

    try:
        d = device.Device(device_uri, printer_name)
    except Error:
        log.error("Unexpected error. Exiting.")
        sys.exit(1)

    log.info("")
    log.info(log.bold(d.device_uri))
    log.info("")

    try:
        try:
            d.open()
            d.queryDevice()
        except Error as e:
            log.error("Error opening device (%s)." % e.msg)
            #sys.exit(1)

        dq_keys = list(d.dq.keys())
        dq_keys.sort()

        log.info(log.bold("Device Parameters (dynamic data):"))
        log.info(log.bold(formatter.compose(("Parameter", "Value(s)"))))
        log.info(formatter.compose(('-'*28, '-'*58)))

        for key in dq_keys:
            log.info(formatter.compose((key, str(d.dq[key]))))

        log.info(log.bold("\nModel Parameters (static data):"))
        log.info(log.bold(formatter.compose(("Parameter", "Value(s)"))))
        log.info(formatter.compose(('-'*28, '-'*58)))

        mq_keys = list(d.mq.keys())
        mq_keys.sort()

        for key in mq_keys:
            log.info(formatter.compose((key, str(d.mq[key]))))

        if d.dbus_avail:
            formatter = utils.TextFormatter(
                            (
                                {'width': 20, 'margin' : 2}, # date/time
                                {'width': 5, 'margin' : 2}, # code
                                {'width': 40, 'margin' : 2}, # desc
                                {'width': 8, 'margin' : 2}, # user
                                {'width': 8, 'margin' : 2}, # job id
                            )
                        )

            log.info(log.bold("\nStatus History (most recent first):"))
            log.info(log.bold(formatter.compose(("Date/Time", "Code", "Status Description", "User", "Job ID"))))
            log.info(formatter.compose(('-'*20, '-'*5, '-'*40, '-'*8, '-'*8)))

            hq = d.queryHistory()

            for h in hq:
                desc = device.queryString(h.event_code)
                log.info(formatter.compose((time.strftime("%x %H:%M:%S", time.localtime(h.timedate)),
                    str(h.event_code), desc, h.username, str(h.job_id))))

            log.info("")
    finally:
        d.close()

    
except KeyboardInterrupt:
    log.error("User exit")

log.info("")
log.info("Done.")

