import cups

def get_devices():
    c = cups.getConnection()
    return c.getDevices()


