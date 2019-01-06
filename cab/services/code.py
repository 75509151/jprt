SUCCESS = 0
FAILED = 1
UNKNOWN_API = 2
MISS_FIELDS = 3
INVALID_FIELDS = 4
UNAVALIABLE_SERVICE = 5
INTERNAL_ERROR = 6

CODE2MSG={
        SUCCESS: "Success",
        FAILED: "Failed",
        UNKNOWN_API: "No Such API",
        MISS_FIELDS: "Miss Fields",
        INVALID_FIELDS: "Invalid Fields",
        UNAVALIABLE_SERVICE: "Service Unavalible"

        }


class NoSuchApiErr(Exception):
    """"""

class MissFieldsErr(Exception):
    """ """

class InvalidFiledsErr(Exception):
    """ """

class InternalErr(Exception):
    """ """
