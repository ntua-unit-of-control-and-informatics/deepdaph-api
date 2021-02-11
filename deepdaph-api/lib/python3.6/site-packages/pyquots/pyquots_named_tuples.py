from collections import namedtuple

QuotsUser = namedtuple('User', [
    'id',
    'email',
    'username',
    'credits',
    'spenton',
    ])

QuotsUser.__new__.__defaults__ = (None,) * len(QuotsUser._fields)

CanProceed = namedtuple('CanProceed', [
    'userid',
    'proceed'
])

ErrorReport = namedtuple('ErrorReport', [
    'message',
    'status'
])

