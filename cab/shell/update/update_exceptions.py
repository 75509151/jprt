# -*- coding: UTF-8 -*-
"""
Created on 2017-08-14

@author: jay
"""


class CmdFailedExecetion(Exception):
    """docstring for CmdFailedExecetion"""


class RsyncException(Exception):
    pass


class ConfigException(Exception):
    pass


class FilelockException(Exception):
    pass


class VersionException(Exception):
    pass


class FirmwareException(Exception):
    pass


class MigrationException(Exception):
    pass
