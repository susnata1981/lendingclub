class TransactionView:
    def __init__(self, type=None, status=None, amount=None, date=None, details=None):
        self.type = type
        self.status = status
        self.amount = amount
        self.date = date
        self.details = details

    def to_map(self):
        rt = self.__dict__
        if self.details:
            dt = []
            for detail in self.details:
                dt.append(detail.to_map())
            rt['details'] = dt
        return rt

class TransactionDetailView:
    def __init__(self, type=None, amount=None):
        self.type = type
        self.amount = amount

    def to_map(self):
        return self.__dict__
