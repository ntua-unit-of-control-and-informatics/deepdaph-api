import http.client as client
from urllib.parse import urlparse
import json
from collections import namedtuple
from .pyquots_named_tuples import *
from .errors import *
import abc


class IPyquots(metaclass=abc.ABCMeta):

    """ Fetch an quots user from the quots application

    Args:
      userid : id of the user as a string
    Returns:
      A QuotsUser named tuple
    Raises:
      UserNotFoundError
    """
    @abc.abstractmethod
    def get_user(self, userid) -> QuotsUser:
        pass

    """ Creates a quots user to teh quots app
    Args:
      quots_user : QuotsUser named tuple
    Returns:
      A QuotsUser named tuple of the user created
    Raises:
      QuotsError
    """
    @abc.abstractmethod
    def create_user(self, quots_user) -> QuotsUser:
        pass

    """ Checks is a user can proceed 
    Args:
      userid : id of the user as a string
      usagetype : The type of usage that we wish to see if a user can proceed
      usagesize : The size of the usage
    Returns:
      A CanProceed named tuple
    Raises:
      CannotProceedError
    """
    @abc.abstractmethod
    def can_user_proceed(self, userid, usagetype, usagesize) -> CanProceed:
        pass

    """ Updates a quots user credits. The passed credits will be the new user's credits!
    Args:
      quots_user : QuotsUser named tuple
    Returns:
      A QuotsUser named tuple of the user created
    Raises:
      QuotsError
    """
    @abc.abstractmethod
    def update_user_credits(self, quotsuser) -> CanProceed:
        pass

    """ Deletes a quots user.
    Args:
      userid : Quots user id
    Returns:
      True if used deleted
    Raises:
      QuotsError
    """
    @abc.abstractmethod
    def delete_user(self, userid) -> True:
        pass


class Pyquots(IPyquots):

    def __init__(self, quotsurl, appid, appsecret):
        self.quotsurl = quotsurl
        self.appid = appid
        self.appsecret = appsecret
        self.conn = self.create_connection()
        self.headers = {
            "Authorization": "QUOTSAPP", "app-id": self.appid
            , "app-secret": self.appsecret}

    def create_connection(self):
        schema = urlparse(self.quotsurl).scheme
        url = urlparse(self.quotsurl).netloc
        if schema == "https":
            return client.HTTPSConnection(url)
        else:
            return client.HTTPConnection(url)

    def get_user(self, userid):
        path = "/users/" + userid
        con = client.HTTPConnection(self.quotsurl)
        headers = {
            "Authorization": "QUOTSAPP", "app-id": self.appid
            , "app-secret": self.appsecret}
        con.request("GET", path, headers=headers)
        r1 = con.getresponse()
        if r1.status < 300:
            raw_data = r1.read()
            encoded = r1.info().get_content_charset('utf8')
            jsonon = json.loads(raw_data.decode(encoded))
            con.close()
            nameduser = QuotsUser(id=jsonon['id'], email=jsonon['email'], username=jsonon['username']
                                     , credits=jsonon['credits'], spenton=jsonon['spenton'])
        else:
            con.close()
            raise UserNotFound("Cannot find user", r1.status)
        return nameduser

    def create_user(self, quotsuser):
        user_json = json.dumps(quotsuser._asdict())
        path = "/users"
        con = client.HTTPConnection(self.quotsurl)
        headers = {
            "Authorization": "QUOTSAPP", "app-id": self.appid
            , "app-secret": self.appsecret}
        con.request("POST", path, body=user_json, headers=headers)
        r1 = con.getresponse()
        if r1.status < 300:
            raw_data = r1.read()
            encoded = r1.info().get_content_charset('utf8')
            jsonon = json.loads(raw_data.decode(encoded))
            con.close()
            nameduser = QuotsUser(id=jsonon['id'], email=jsonon['email'], username=jsonon['username']
                                     , credits=jsonon['credits'], spenton=jsonon['spenton'])
        else:
            raw_data = r1.read()
            encoded = r1.info().get_content_charset('utf8')
            jsonon = json.loads(raw_data.decode(encoded))
            con.close()
            raise QuotsError(jsonon["message"], r1.status)
        return nameduser

    def can_user_proceed(self, userid, usagetype, usagesize):
        path = "/users/{}/quots?appid={}&usage={}&size={}".format(userid, self.appid, usagetype, usagesize)
        con = client.HTTPConnection(self.quotsurl)
        headers = {
            "Authorization": "QUOTSAPP", "app-id": self.appid
            , "app-secret": self.appsecret}
        con.request("GET", path, headers=headers)
        r1 = con.getresponse()
        if r1.status < 300:
            raw_data = r1.read()
            encoded = r1.info().get_content_charset('utf8')
            jsonon = json.loads(raw_data.decode(encoded))
            con.close()
            can_proc = CanProceed(userid=jsonon["userid"], proceed=jsonon['proceed'])
        else:
            raw_data = r1.read()
            encoded = r1.info().get_content_charset('utf8')
            jsonon = json.loads(raw_data.decode(encoded))
            con.close()
            raise CannotProceedError(jsonon["message"], r1.status)
        return can_proc

    def update_user_credits(self, quotsuser):
        user_json = json.dumps(quotsuser._asdict())
        path = "/users/credits"
        con = client.HTTPConnection(self.quotsurl)
        headers = {
            "Authorization": "QUOTSAPP", "app-id": self.appid
            , "app-secret": self.appsecret}
        con.request("PUT", path, body=user_json, headers=headers)
        r1 = con.getresponse()
        if r1.status < 300:
            raw_data = r1.read()
            encoded = r1.info().get_content_charset('utf8')
            jsonon = json.loads(raw_data.decode(encoded))
            con.close()
            nameduser = QuotsUser(id=jsonon['id'], email=jsonon['email'], username=jsonon['username']
                                     , credits=jsonon['credits'], spenton=jsonon['spenton'])
        else:
            raw_data = r1.read()
            encoded = r1.info().get_content_charset('utf8')
            jsonon = json.loads(raw_data.decode(encoded))
            con.close()
            raise QuotsError(jsonon["message"], r1.status)
        return nameduser

    def delete_user(self, userid):
        path = "/users/" + userid
        con = client.HTTPConnection(self.quotsurl)
        headers = {
            "Authorization": "QUOTSAPP", "app-id": self.appid
            , "app-secret": self.appsecret}
        con.request("DELETE", path, headers=headers)
        r1 = con.getresponse()
        if r1.status == 410:
            con.close()
            return True
        else:
            raw_data = r1.read()
            encoded = r1.info().get_content_charset('utf8')
            jsonon = json.loads(raw_data.decode(encoded))
            con.close()
            raise QuotsError(jsonon["message"], r1.status)

    def close(self):
        self.conn.close()
