def render(table, params):
    # if no column has been selected, return table
    if not params['colnames'] or not params['to_replace']:
        return table

    to_replace = params['to_replace']
    match_case = params['match_case']
    match_entire = params['match_entire']
    replace_with = params['replace_with']
    regex = params['regex']
    columns = params['colnames'].split(',')
    columns = [c.strip() for c in columns]

    # Detect if input is a number or string
    try:
        replace_with = int(replace_with)
    except ValueError:
        pass

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

    for column in columns:
        if pd.api.types.infer_dtype(table[column]) != 'categorical':
            # Convert column to string (or retain category) if regex
            dtype = table[column].dtype
            table[column] = table[column].astype(str).replace(pattern, str(replace_with))
            # try to convert back to dtype
            table[column] = table[column].astype(dtype, errors='ignore')

        # for categories, perform replace on index
        else:
            # All to string for now, .replace does not work on numerical categories
            cat_dtype = table[column].cat.categories.dtype
            new_index = pd.Series(table[column].cat.categories).astype(str).replace(pattern, str(replace_with))
            # Check if duplicates
            if not any(new_index.duplicated()):
                # Try to cast back to original dtype
                try:
                    table[column] = table[column].cat.rename_categories(new_index.astype(cat_dtype))
                except (TypeError, ValueError):
                    table[column] = table[column].cat.rename_categories(new_index)
            else:
                category_mask = table[column].cat.categories.str.contains(pattern)
                diff = set(new_index) - set(table[column].cat.categories)
                table[column].cat.add_categories(diff, inplace=True)
                series_index = table[column].cat.codes[lambda x: category_mask[x]].index

                table[column].iloc[series_index] = table[column][series_index].str.replace(pattern, str(replace_with))
                table[column].cat.remove_unused_categories(inplace=True)

    return table
