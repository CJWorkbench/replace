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
        value = wf_module.get_param_string('value')
        df = table.replace(to_replace, value)
        return df