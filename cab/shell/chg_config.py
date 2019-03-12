#!/home/zz/.pyenv/shims/python


import os
import time
from optparse import OptionParser
from cab.utils.c_log import init_log
from cab.utils.machine_info import get_machine_id
from cab.db.dbm import get_db_instance

log = init_log("change_config")

NOT_SHOW_LIST = ()


def change_config(key, value):
    try:
        db = get_db_instance()
        sql = "SELECT id_ai, key, value FROM machine_config;"
        configs = [itm for itm in db.cursor.execute(sql) if itm[1] not in NOT_SHOW_LIST]
        configs = sorted(configs, key=lambda x: x[1])
        list_all = True
        if key:
            keys = [itm[1] for itm in configs]
            if key in keys:
                list_all = False
                select_id = keys.index(key)
                confirm = input("Are your sure to change config(%s) to %s? y/N: " % (key, value))
                if confirm.lower() not in ("y", "yes"):
                    os.abort()
            else:
                print ("Invalid Key:", key)
                print ("All configs will be listed in 2 seconds...")
                time.sleep(2)

        if list_all:
            print ("All configs...")
            print ("\033[1;32m%s\033[0m" % ("%-4s%-30s%s" % ("ID", "Key", "Value")))
            ids = range(len(configs))
            for i in ids:
                print ("%-4s%-30s%s" % (i, configs[i][1], configs[i][2]))

            select_id = input("Please input the config ID which to be changed: ")
            try:
                select_id = int(select_id)
            except ValueError:
                print ('DoNOT test me!! I am NOT baby!')
                print ('I just need a number')
                os.abort()

            if select_id not in ids:
                print ('The number is out of my range!')
                os.abort()

            key = configs[select_id][1]
            print ("The old value of config(%s) is: %s." % (key, configs[select_id][2]))
            value = input("Please input the new value: ")

        db.set_kv("machine_config", {key: value})

        msg = "Changed the config(%s) from %s to %s successfully." % (key, configs[select_id][2], value)
        print (msg)
        log.info(msg)
    except Exception as ex:
        log.error("%s %s: %s" % (key, value, ex))
        raise


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-k", "--key", dest="key", default="",
                      help="The config name which to be changed")
    parser.add_option("-v", "--value", dest="value", default="",
                      help="The config value which to be changed to")
    (options, args) = parser.parse_args()
    key = options.key
    value = options.value
    change_config(key, value)
