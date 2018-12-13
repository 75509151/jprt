import cups

def get_printers():
    conn = cups.Connection()
    return conn


