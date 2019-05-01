from dataclasses import dataclass
import re
from typing import List
import pandas as pd


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
            regex = r'\A' + regex + r'\Z'
        if self.match_case:
            flags = 0
        else:
            flags = re.IGNORECASE
        self._regex = re.compile(regex, flags)

    @classmethod
    def parse(cls, *, colnames: str, **kwargs):
        if not colnames:
            colnames = []
        else:
            colnames = colnames.split(',')
        return cls(colnames=colnames, **kwargs)

    def process_table(self, table: pd.DataFrame) -> pd.DataFrame:
        for column in self.colnames:
            table[column] = self.process_series(table[column])
        return table

    def process_series(self, series: pd.Series) -> pd.Series:
        if hasattr(series, 'cat'):
            return self._process_categorical(series)
        else:
            return self._process_str(series)

    def _process_categorical(self, series: pd.Series) -> pd.Series:
        # Replace categorical directly, so we only inspect each string once and
        # we don't consume much RAM.

        # Categories are Arrays -- meaning they map "code" -> "category"
        old_categories = series.cat.categories
        # new_categories_with_dups has new "category" values but same "codes"
        new_categories_with_dups = (
            series.cat.categories
            .str.replace(self._regex, self.replace_with)
        )
        # new_categories: the categories we want in the end.
        # We want them sorted, because unit tests care.
        new_categories = new_categories_with_dups.unique().sort_values()

        # invert "new_categories": we'll map from "new_category" -> "code"
        new_category_to_code = dict(zip(new_categories, range(len(new_categories))))

        # map from old-"code" to new-"code". Remember: new_categories_with_dups
        # uses the old "codes".
        code_renames = new_categories_with_dups.map(new_category_to_code)

        new_codes = code_renames[series.cat.codes]

        ret = pd.Categorical.from_codes(new_codes, new_categories)
        return ret

    def _process_str(self, series: pd.Series) -> pd.Series:
        return series.replace(self._regex, self.replace_with)


def render(table, params):
    try:
        form = Form.parse(**params)
    except re.error as err:
        return 'Invalid regular expression: ' + str(err)

    if not form.colnames or not form.to_replace:
        # if no column has been selected, return table
        return table

    return form.process_table(table)


def _migrate_params_v0_to_v1(params):
    """v0: colnames is comma-separated str. v1: colnames is List[str]."""
    return {
        **params,
        'colnames': [c for c in params['colnames'].split(',') if c],
    }


def migrate_params(params):
    if isinstance(params['colnames'], str):
        params = _migrate_params_v0_to_v1(params)
    return params
