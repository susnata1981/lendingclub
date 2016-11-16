#Exceptions
class ZipllyError(Exception):
    def __init__(self, message=None, orig_exp=None):
        super(ZipllyError, self).__init__(message)
        self.orig_exp = orig_exp

class StripeError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(StripeError, self).__init__(message=message, orig_exp=orig_exp)

class DatabaseError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(DatabaseError, self).__init__(message=message, orig_exp=orig_exp)

class UserInputError(ZipllyError):
    def __init__(self, message=None, param=None, orig_exp=None,):
        super(UserInputError, self).__init__(message=message, orig_exp=orig_exp)
        self.param=param

class ValidationError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(ValidationError, self).__init__(message=message, orig_exp=orig_exp)

class AccountExistsError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(AccountExistsError, self).__init__(message=message, orig_exp=orig_exp)

class AccountNotFoundError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(AccountNotFoundError, self).__init__(message=message, orig_exp=orig_exp)

class AccountEmailAlreadyVerifiedError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(AccountEmailAlreadyVerifiedError, self).__init__(message=message, orig_exp=orig_exp)

class EmailVerificationNotMatchError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(EmailVerificationNotMatchError, self).__init__(message=message, orig_exp=orig_exp)

class MailServiceError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(MailServiceError, self).__init__(message=message, orig_exp=orig_exp)

class EmailVerificationSendingError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(EmailVerificationNotMatchError, self).__init__(message=message, orig_exp=orig_exp)

class EmailVerificationRequiredError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(EmailVerificationRequiredError, self).__init__(message=message, orig_exp=orig_exp)

class InvalidLoginCredentialsError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(InvalidLoginCredentialsError, self).__init__(message=message, orig_exp=orig_exp)

class PlaidBankInfoFetchError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(PlaidBankInfoFetchError, self).__init__(message=message, orig_exp=orig_exp)

class BankAlreadyVerifiedError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(BankAlreadyVerifiedError, self).__init__(message=message, orig_exp=orig_exp)

class IncorrectRandomDepositAmountsError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(IncorrectRandomDepositAmountsError, self).__init__(message=message, orig_exp=orig_exp)

class BankAlreadyExistsError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(BankAlreadyExistsError, self).__init__(message=message, orig_exp=orig_exp)

class PasswordResetTokenNotMatchError(ZipllyError):
    def __init__(self, message=None, orig_exp=None):
        super(PasswordResetTokenNotMatchError, self).__init__(message=message, orig_exp=orig_exp)
