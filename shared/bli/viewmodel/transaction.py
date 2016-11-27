from shared.db.model import TransactionDetail
from pprint import pprint


class TransactionView:

    def __init__(self, loan_id=None, type=None, status=None, amount=None, date=None, details=None):
        self.loan_id = loan_id
        self.type = type
        self.status = status
        self.amount = amount
        self.date = date
        self.details = details

    def to_map(self):
        rt = dict(self.__dict__)
        if self.details:
            dt = []
            for detail in self.details:
                dt.append(detail.to_map())
            rt['details'] = dt
        # removing loan_id so that this value is not sent to front end
        rt.pop('loan_id', None)
        return rt


class TransactionDetailView:
    TYPE_DESCRIPTION = {TransactionDetail.INTEREST: 'Interest', TransactionDetail.PRINCIPAL: 'Principal',
                        TransactionDetail.LATE_FEE: 'Late Fees', TransactionDetail.LATE_INTEREST: 'Interest charged for late payments'}

    def __init__(self, type=None, amount=None):
        self.type = type
        self.amount = amount

    def to_map(self):
        rt = dict(self.__dict__)
        rt['type'] = TransactionDetailView.TYPE_DESCRIPTION[self.type]
        return rt
