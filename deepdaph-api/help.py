import random
import string

# epoch = datetime.utcfromtimestamp(0)
#
#
# def unix_time_millis(dt):
#     return (dt - epoch).total_seconds() * 1000.0
#
#
# def utc_to_local(utc_dt):
#     return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None).replace(tzinfo=None)


def randomString(stringLength=10):
    """Generate a random string of letters, digits """
    password_characters = string.ascii_letters + string.digits + string.ascii_letters + string.digits
    return ''.join(random.choice(password_characters) for i in range(stringLength))


s = 'Fri Apr 10 2020 00:00:00 GMT+0300'
# s = "Thu Apr 09 2020 00:00:00 GMT 0300 (Eastern European Summer Time)"
#
# datep.parse(s)
# d = datetime.strptime(s, '%a %b %d %Y %H:%M:%S %Z%z')
# print(d)
# print(utc_to_local(d))
# to_d = unix_time_millis(utc_to_local(datetime.strptime(s, '%a %b %d %Y %H:%M:%S %Z%z')))
# print(to_d)
# print(to_d)
