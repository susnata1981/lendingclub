import json

class Notification:
    # NOTIFICATION_TYPE
    SUCCESS, WARNING, NORMAL, ERROR = range(4)

    def __init__(self, title, notification_type, description=None, url1=None, url2=None):
        self.title = title
        self.description = description
        self.notification_type = notification_type
        self.clazz = self.get_css_class()
        self.url1 = url1
        self.url2 = url2

    def get_css_class(self):
        if self.notification_type == Notification.SUCCESS or self.notification_type == Notification.NORMAL:
            return 'alert-success'
        elif self.notification_type == Notification.WARNING:
            return 'alert-warning'
        elif self.notification_type == Notification.ERROR:
            return 'alert-danger'

    def to_map(self):
        return self.__dict__
