

class PrtManager(object):
    def __init__(self):
        pass

    def get_printer(self):
        pass

    def check_printer(self):
        self._check_and_install()
        self._check_and_report_params()
        self.check_and_report_status()


    def _check_and_install(self):
        pass

    def _check_and_report_params(self):
        pass

    def check_and_report_status(self):
        pass

    def print_file(self, document):
        pass
    

    def report_print_result(self):
        pass
