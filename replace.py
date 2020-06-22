from dataclasses import dataclass
import re
import sre_parse
from typing import List
import numpy as np
import pandas as pd
from cjwmodule import i18n


class RegexError(Exception):
    pass


@dataclass
class Form:
    to_replace: str
    replace_with: str
    match_case: bool
    match_entire: bool
    regex: bool
    colnames: List[str]

    def __post_init__(self):
        # set self._regex, the re.Pattern we'll pass to pandas.
        if self.regex:
            regex = self.to_replace
        else:
            regex = re.escape(self.to_replace)
        if self.match_entire:
            regex = r"\A" + regex + r"\Z"
        if self.match_case:
            flags = 0
        else:
            flags = re.IGNORECASE

        errors = []
        try:
            self._regex = re.compile(regex, flags)
        except re.error as err:
            raise RegexError(
                i18n.trans(
                    "error.regex.general",
                    "Invalid regular expression: {error}",
                    {"error": str(err)},
                )
            ) from None

        if self.regex:
            # With a regex, "Replace With" is a template. It may have a "\1" or
            # some-such; so we can only detect errors after the template is
            # compiled.
            #
            # sre_parse.parse_template() will actually be invoked by Python's
            # `re` module for each value. We run it one extra time here to
            # generate the error message if there is one.
            #
            # [2020-06-17, adamhooper] `sre_parse.expand_template` seems to be
            # the logic we want, dammit: compile the template once, then reuse
            # it on each row. TODO benchmark and maybe submit a pull request to
            # Pandas (or rewrite using re._subx and Pyarrow).
            try:
                sre_parse.parse_template(self.replace_with, self._regex)
                self._repl = self.replace_with
            except re.error as err:
                raise RegexError(
                    i18n.trans(
                        "error.replace_with.template",
                        "Invalid replacement template: {error}",
                        {"error": str(err)},
                    )
                ) from None
        else:
            # Pandas is going to pass `replace_with` as the repl argument to
            # re.sub(). That's soooooo annoying, because repl doesn't behave
            # like a string.
            #
            # https://docs.python.org/3/library/re.html#re.sub:
            #
            # repl can be a string or a function; if it is a string, any
            # backslash escapes in it are processed. That is, \n is converted
            # to a single newline character, \r is converted to a carriage
            # return, and so forth. Unknown escapes of ASCII letters are
            # reserved for future use and treated as errors. Other unknown
            # escapes such as \& are left alone.
            self._repl = self.replace_with.replace("\\", "\\\\")

    def process_table(self, table: pd.DataFrame) -> pd.DataFrame:
        for column in self.colnames:
            table[column] = self.process_series(table[column])
        return table

    def process_series(self, series: pd.Series) -> pd.Series:
        if hasattr(series, "cat"):
            return self._process_categorical(series)
        else:
            return self._process_str(series)

    def _process_categorical(self, series: pd.Series) -> pd.Series:
        # Replace categorical directly, so we only inspect each string once and
        # we don't consume much RAM.

        # Categories are Arrays -- meaning they map "code" -> "category"
        old_categories = series.cat.categories
        # new_categories_with_dups has new "category" values but same "codes"
        new_categories_with_dups = series.cat.categories.str.replace(
            self._regex, self._repl
        )
        # new_categories: the categories we want in the end.
        # We want them sorted, because unit tests care.
        new_categories = new_categories_with_dups.unique().sort_values()

        # invert "new_categories": we'll map from "new_category" -> "code"
        new_category_to_code = dict(zip(new_categories, range(len(new_categories))))

        # map from old-"code" to new-"code". Remember: new_categories_with_dups
        # uses the old "codes".
        code_renames = new_categories_with_dups.map(new_category_to_code)
        code_renames_with_null = np.append(code_renames.values, [-1])

        new_codes = code_renames_with_null[series.cat.codes]

        ret = pd.Categorical.from_codes(new_codes, new_categories)
        return ret

    def _process_str(self, series: pd.Series) -> pd.Series:
        return series.replace(self._regex, self._repl)


def render(table, params):
    try:
        form = Form(**params)
    except RegexError as err:
        return err.args[0]

    if not form.to_replace and not form.match_entire:
        # User did not enter a search term
        return table

    return form.process_table(table)


def _migrate_params_v0_to_v1(params):
    """v0: colnames is comma-separated str. v1: colnames is List[str]."""
    return {**params, "colnames": [c for c in params["colnames"].split(",") if c]}


def migrate_params(params):
    if isinstance(params["colnames"], str):
        params = _migrate_params_v0_to_v1(params)
    return params
