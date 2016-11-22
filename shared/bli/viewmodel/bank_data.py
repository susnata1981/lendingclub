class BankData:
    def __init__(self, account_number, routing_number, currency, \
            country, holder_name, verification_type, status,  usage_status, primary):
        self.account_number = account_number
        self.routing_number = routing_number
        self.currency = currency
        self.country = country
        self.holder_name = holder_name
        self.verification_type = verification_type
        self.status = status
        self.usage_status = usage_status
        self.primary = primary

    def to_map(self):
        return self.__dict__

class BankDepositData:
    def __init__(self, id, deposit1, deposit2):
        self.id = id
        self.deposit1 = deposit1
        self.deposit2 = deposit2
