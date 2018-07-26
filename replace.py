def render(table, params):
    # if no column has been selected, return table
    if not params['colnames']:
        return table

    to_replace = params['to_replace']
    match_case = params['match_case']
    match_entire = params['match_entire']
    replace_with = params['replace_with']
    regex = params['regex']
    columns = params['colnames'].split(',')
    columns = [c.strip() for c in columns]

    if not regex:
        to_replace = re.escape(to_replace)

    else:
        try:
            re.compile(to_replace)
        except re.error:
            raise ValueError('Invalid regular expression')

    if match_entire:
        to_replace = '^' + to_replace + '$'

    if match_case:
        pattern = re.compile(to_replace)
    else:
        pattern = re.compile(to_replace, re.IGNORECASE)

    table[columns] = table[columns].astype(str).replace(pattern, replace_with)
    return table
