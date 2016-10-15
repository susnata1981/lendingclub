#Exceptions

class UserInputError(Exception):
    def __init__(self, message=None, param=None):
        super(UserInputError, self).__init__(message)
        self.param=param

class ValidationError(Exception):
    def __init__(self, message=None):
        super(ValidationError, self).__init__(message)

class SystemError(Exception):
    def __init__(self, display_message=None, actual_message=None):
        super(UserInputError, self).__init__(display_message)
        self.my_message = actual_message

