import json

class Notification:
    # NOTIFICATION_TYPE
    SUCCESS, WARNING, NORMAL, ERROR = range(4)

    def __init__(self, title, clazz, notification_type, description=None, url1=None, url2=None):
        self.title = title
        self.description = description
        self.clazz = clazz
        self.notification_type = notification_type
        self.url1 = url1
        self.url2 = url2

    def to_map(self):
        return self.__dict__
