import collections

class OnboardingStepVM:
    PERSONAL_INFORMATION, ENTER_EMPLOYER_INFORMATION, LINK_BANK_ACCOUNT, VERIFY_BANK_ACCOUNT, APPLY_LOAN = range(5)

    STEPS = [
        {
            'id': PERSONAL_INFORMATION,
            'name': 'Enter personal information'
        },
        {
            'id': ENTER_EMPLOYER_INFORMATION,
            'name': 'Enter employer information'
        },
        {   'id': LINK_BANK_ACCOUNT,
            'name': 'Link your bank'
        },
        {
            'id': VERIFY_BANK_ACCOUNT,
            'name': 'Verify your bank'
        },
        {
            'id': APPLY_LOAN,
            'name': 'Apply for loan'
        }
    ]

    def __init__(self):
        self.signup_steps = collections.OrderedDict()
        self.init_signup_steps()

        self.onboarding_steps = collections.OrderedDict()
        self.init_onboarding_steps()

        # additional data for some of the steps
        self.verify_bank_id = None

    def init_signup_steps(self):
        for step in OnboardingStepVM.STEPS:
            self.signup_steps[step['id']] = Step(
            name=step['name'],
            completed = False,
            is_active=False)

    def is_complete(self, id):
        return self.signup_steps[id].completed

    def init_onboarding_steps(self):
        for step in OnboardingStepVM.STEPS[1:]:
            self.onboarding_steps[step['id']] = Step(
            name=step['name'],
            completed = False,
            is_active=False)

    def set_onboarding_state(self, id, is_active):
        self.onboarding_steps[id].is_active = is_active

    def set_signup_state(self, id, completed):
        self.signup_steps[id].completed = completed

    def get_onboarding_steps(self):
        result = []
        for step_id in self.onboarding_steps:
            os = self.onboarding_steps[step_id]
            result.append(os.__dict__)
        return result

    def get_signup_steps(self):
        result = []
        for step_id in self.signup_steps:
            os = self.signup_steps[step_id]
            result.append(os.__dict__)
        return result

class Step:
    def __init__(self, name, completed, is_active):
        self.name = name
        self.completed = completed
        self.is_active = is_active
