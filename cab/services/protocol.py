import struct
import json
import uuid
import time

#                    Configuration.
# ======================================================
STX = 0x66554433
ETX = 0x77889911

MSG_TYPE_REQUEST = 0x01
MSG_TYPE_REPLY = 0x02
MSG_TYPE_BATCH_REQUEST = 0x03
MSG_TYPE_VALIDATE_CHALLENGE = 0x04
MSG_TYPE_VALIDATE_CONNECTION = 0x05
MSG_TYPE_CLOSE = 0x06
MSG_TYPE_UNKNOWN = 0xff


TRANSPORT_CLOSED = 0
TRANSPORT_CONNECTED = 1
TRANSPORT_CLOSING = 2

DEFAULT_TIMEOUT = 15  # second

MAX_MESSAGE_LENGTH = 10485760  # 10M

# ======================================================
#                    Exception
# ======================================================


class BaseException(Exception):
    def __init__(self, msg=""):
        Exception.__init__(self, msg)


class ProtocolException(BaseException):
    def __init__(self, msg=""):
        BaseException.__init__(self, msg)


class CodecException(BaseException):
    def __init__(self, msg=""):
        BaseException.__init__(self, msg)


class CommunicateException(BaseException):
    def __init__(self, msg=""):
        BaseException.__init__(self, msg)


class UnkownException(BaseException):
    def __init__(self, msg=""):
        BaseException.__init__(self, msg)


class NoMethodException(BaseException):
    def __init__(self, msg=""):
        BaseException.__init__(self, msg)


class UserException(BaseException):
    def __init__(self, msg=""):
        BaseException.__init__(self, msg)

# ======================================================
#                    BaseObj
# ======================================================


class AgentBase(object):
    """ Base object.
    """

    def __init__(self, _uuid=None):
        if _uuid:
            self._id = _uuid
        else:
            self._id = str(uuid.uuid4())

    def _get_id(self):
        return self._id

# ======================================================
#      Protocol, DCECodec, Request, Reply
# ======================================================


class AgentCodec(AgentBase):
    """ Codec """

    def __init__(self):
        AgentBase.__init__(self)

    def encode_request(self, _id, func, params):
        try:
            return json.dumps({"id": _id,
                                "func":func,
                               "params": params
                               }).encode()
        except Exception as ex:
            raise CodecException(str(ex))

    def encode_reply(self, _id, func, params):
        try:
            return json.dumps({"id": _id,
                                "func":func,
                               "params": params
                               })
        except Exception as ex:
            raise CodecException(str(ex))


    def decode(self, msg):
        try:
            return json.loads(msg)
        except Exception as ex:
            raise CodecException(str(ex))


class Request(AgentBase):
    """ Request """

    def __init__(self, method_name, params, one_way=0, _type=MSG_TYPE_REQUEST):
        AgentBase.__init__(self)
        self._method_name = method_name
        self._params = params
        self._one_way = one_way
        self._type = _type


class Reply(AgentBase):
    """ Reply """

    def __init__(self, reqId, status, body, _type=MSG_TYPE_REPLY):
        AgentBase.__init__(self)
        self._rid = reqId
        self._status = status
        self._body = body
        self._type = _type


class Protocol(object):
    """ Protocol of Agent. """
    head_fmt = ">IBQ"
    head_size = struct.calcsize(head_fmt)
    tail_fmt = ">I"
    tail = struct.pack(tail_fmt, ETX)

    def __init__(self):
        pass

    def request_to_raw(self, req):
        if req._one_way:
            _id = "00000000-0000-0000-0000-000000000000"
        else:
            _id = str(req._id)
        codec = AgentCodec()
        body = codec.encode_request(_id, req._method_name, req._params)
        l = len(body)
        # binary_body = struct.pack("%ss" % l, body)
        # print "body in request_to_raw: %s %s" % (l, body)
        head = struct.pack(self.head_fmt, STX, req._type, len(body))
        # print "head in request_to_raw:", head
        request_bytes = head + body + self.tail

        return (_id, request_bytes)

    def reply_to_raw(self, reply):
        codec = AgentCodec()
        body = codec.encode_reply(reply._rid, reply._status, reply._body)
        l = len(body)
        binary_body = struct.pack("%ss" % l, body)
        # print "body in reply_to_raw: %s %s" % (l, body)
        head = struct.pack(self.head_fmt, STX, reply._type, l)
        # print "head in reply_to_raw:", head
        # return head + binary_body + self.tail
        return head.encode()

    def parse_head(self, head):
        try:
            head_info = struct.unpack(self.head_fmt, head)

            if head_info[0] != STX:
                raise ProtocolException("Magic number error")

            codec = AgentCodec()
            # (type,bodysize,codec)
            return (head_info[1], head_info[2], codec)
        except Exception as ex:
            raise ProtocolException(str(ex))

    def get_head_size(self):
        return self.head_size
