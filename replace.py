def render(table, params):
    to_replace = params['to_replace']
    match_case = params['match_case']
    match_entire = params['match_entire']
    value = params['value']

    to_replace = re.escape(to_replace)
    if match_entire:
        to_replace = '^' + to_replace + '$'

    if match_case:
        pattern = re.compile(to_replace)
    else:
        pattern = re.compile(to_replace, re.IGNORECASE)

    df = table.replace(pattern, value)
    return df
