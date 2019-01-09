class PrtError(Exception):
    code = 2000
    msg = ""

class PrtSetupError(Exception):
    code = 2001
    msg = "Printer Setup Failed"

class DeviceNotFoundError(Exception):
    code = 2002
    msg = "Device Not Found"

class PrtPrintError(Exception):
    code = 2003
    msg = "Print File Failed"
