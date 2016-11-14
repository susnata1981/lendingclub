#Exceptions

class StripeError(Exception):
    def __init__(self, display_message=None, orig_exp=None):
        super(StripeError, self).__init__(display_message)
        self.orig_exp = orig_exp

class DatabaseError(Exception):
    def __init__(self, display_message=None, orig_exp=None):
        super(DatabaseError, self).__init__(display_message)
        self.orig_exp = orig_exp

class UserInputError(Exception):
    def __init__(self, message=None, orig_exp=None, param=None):
        super(UserInputError, self).__init__(message)
        self.param=param
        self.orig_exp = orig_exp

class ValidationError(Exception):
    def __init__(self, message=None, orig_exp=None):
        super(ValidationError, self).__init__(message)

class AccountExistsError(Exception):
    def __init__(self, message=None, orig_exp=None):
        super(AccountExistsError, self).__init__(message)

class AccountNotFoundError(Exception):
    def __init__(self, message=None, orig_exp=None):
        super(AccountNotFoundError, self).__init__(message)

class AccountEmailAlreadyVerifiedError(Exception):
    def __init__(self, message=None, orig_exp=None):
        super(AccountEmailAlreadyVerifiedError, self).__init__(message)

class EmailVerificationNotMatchError(Exception):
    def __init__(self, message=None, orig_exp=None):
        super(EmailVerificationNotMatchError, self).__init__(message)

class MailServiceError(Exception):
    def __init__(self, message=None, orig_exp=None):
        super(MailServiceError, self).__init__(message)

class EmailVerificationSendingError(Exception):
    def __init__(self, message=None, orig_exp=None):
        super(EmailVerificationNotMatchError, self).__init__(message)
