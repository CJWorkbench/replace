import re

class Importable:
    @staticmethod
    def __init__(self):
        pass

    @staticmethod
    def event():
        pass

    @staticmethod
    def render(wf_module, table):
        to_replace = wf_module.get_param_string('to_replace')
        match_case = wf_module.get_param_checkbox("match_case")
        match_entire = wf_module.get_param_checkbox("match_entire")
        value = wf_module.get_param_string('value')

        to_replace = re.escape(to_replace)
        if match_entire:
            to_replace = '^' + to_replace + '$'

        if match_case:
            pattern = re.compile(to_replace)
        else:
            pattern = re.compile(to_replace, re.IGNORECASE)

        df = table.replace(pattern, value)
        return df