
class SignupSteps:
    ORDER = ['personal_information', 'employer_information', 'add_bank', 'verify_bank', 'apply_loan']
    def __init__(self):
        # A True indicates that the step is completed.
        # The values are initialized to True and the
        # accountBLI sets these value appropriately when return an object of this calss.
        self.personal_information = True
        self.employer_information = True
        self.add_bank = True
        self.verify_bank = True
        self.apply_loan = True

        #additional data for some of the steps
        self.verify_bank_id = None

    def to_map(self):
        var_map = self.__dict__
        steps = []
        for key in SignupSteps.ORDER:
            steps.append({
                'title': key,
                'done': var_map[key]
            })
        return {'steps': steps}
