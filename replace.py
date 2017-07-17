class Importable:
    @staticmethod
    def event():
        pass

    @staticmethod
    def render(wf_module, table):
        to_replace = wf_module.get_param_string('to_replace')
        value = wf_module.get_param_string('value')
        df = table.replace(to_replace, value)
        return df