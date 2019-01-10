SUCCESS = 0
FAILED = 1
UNKNOWN_API = 2
MISS_FIELDS = 3
INVALID_FIELDS = 4
UNAVALIABLE_SERVICE = 5
INTERNAL_ERROR = 6


DOWNLOAD_ERROR = 1000
UNEXIST_ERROR = 1002
UPLOAD_ERROR = 1003

CODE2MSG={
        SUCCESS: "Success",
        FAILED: "Failed",
        UNKNOWN_API: "No Such API",
        MISS_FIELDS: "Miss Fields",
        INVALID_FIELDS: "Invalid Fields",
        UNAVALIABLE_SERVICE: "Service Unavalible"

        }

class ExternalErr(Exception):
    code = 0
    msg = ""

class NoSuchApiErr(ExternalErr):
    code = UNKNOWN_API
    msg = CODE2MSG[code]

class MissFieldsErr(ExternalErr):
    code = MISS_FIELDS
    msg = CODE2MSG[code]

class InvalidFiledsErr(ExternalErr):
    code = INVALID_FIELDS
    msg = CODE2MSG[code]


class InternalErr(Exception):
    code = INTERNAL_ERROR
    msg = CODE2MSG[code]



class DownloadError(InternalErr):
    code = DOWNLOAD_ERROR
    msg = "file download failed"


class FileUnEixstError(InternalErr):
    code = UNEXIST_ERROR
    msg = "File does not exist"

class UpoloadError(InternalErr):
    code = UpoloadError
    msg = "Upload failed"
