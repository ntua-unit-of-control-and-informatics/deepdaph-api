class Error(Exception):
    pass


class CannotProceedError(Error):
    def __init__(self, message, status):
        self.message = message
        self.status = status


class UserNotFound(Error):
    def __init__(self, message, status):
        self.message = message
        self.status = status


class InternalServerError(Error):
    def __init__(self, message, status):
        self.message = message
        self.status = status


class QuotsError(Error):
    def __init__(self, message, status):
        self.message = message
        self.status = status