import unittest
import pandas as pd
import numpy as np
from replace import render


class TestReplace(unittest.TestCase):

    def setUp(self):
        # Test data includes:
        #  - rows of numeric and string types
        self.table = pd.DataFrame([
            ['AaAfredaAaA', 12333, 3.14, '1964-5-05'],
            ['aAaAfredaAAaaa', 5211111, 45.64, '1964-7-28 08:55'],
            ['AaAfredAaaaA', -323434, 435.00, '1964'],
            ['AAfredAA', 32331, 35331.19, '1964-2-27'],
            ['AaaAfredAaaaA', 8009823, 0.07, '1964-7-30']],
            columns=['stringcol', 'intcol', 'floatcol', 'datecol'])

        # Pandas should infer these types anyway, but leave nothing to chance
        self.table['stringcol'] = self.table['stringcol'].astype(str)
        self.table['intcol'] = self.table['intcol'].astype(np.int64)
        self.table['floatcol'] = self.table['floatcol'].astype(np.float64)
        self.table['datecol'] = self.table['datecol'].astype(str)

    def test_NOP(self):
        params = {'colnames': ''}
        out = render(self.table, params)
        self.assertTrue(out.equals(self.table))  # should NOP when first applied

    def test_regex_str(self):
        # strcol should only contain 'fred'
        params = {
            'colnames': 'stringcol',
            'to_replace': '[a]',
            'match_case': False,
            'regex': True,
            'match_entire': False,
            'replace_with': ''
        }
        out = render(self.table.copy(), params)
        for y in out['stringcol']:
            self.assertTrue(y == 'fred')

        # strcol should only contain 'AAfredAA'
        params = {
            'colnames': 'stringcol',
            'to_replace': '[a]',
            'match_case': True,
            'regex': True,
            'match_entire': False,
            'replace_with': ''
        }
        out = render(self.table.copy(), params)
        for y in out['stringcol']:
            self.assertTrue(y == 'AAfredAA')

            # datecol should only contain '2018'
            params = {
                'colnames': 'datecol',
                'to_replace': '[^1964]',
                'match_case': False,
                'regex': True,
                'match_entire': False,
                'replace_with': ''
            }
            out = render(self.table.copy(), params)
            for y in out['datecol']:
                self.assertTrue(y == '1964')

    def test_regex_num(self):
        # intcol should only contain '2'
        params = {
            'colnames': 'intcol',
            'to_replace': '[0-1|3-9|\D]',
            'match_case': False,
            'regex': True,
            'match_entire': False,
            'replace_with': ''
        }
        out = render(self.table.copy(), params)
        self.assertTrue(out['intcol'].dtype == object)
        for y in out['intcol']:
            self.assertTrue(y == '2')

        # floacol should only contain '2.'
        params = {
            'colnames': 'floatcol',
            'to_replace': '[\d]',
            'match_case': False,
            'regex': True,
            'match_entire': False,
            'replace_with': ''
        }
        out = render(self.table.copy(), params)
        self.assertTrue(out['floatcol'].dtype == object)
        for y in out['floatcol']:
            self.assertTrue(y == '.')

    def test_str_search(self):
        # strcol should not contain 'fred'
        params = {
            'colnames': 'stringcol',
            'to_replace': 'fred',
            'match_case': False,
            'regex': False,
            'match_entire': False,
            'replace_with': ''
        }
        out = render(self.table.copy(), params)
        for y in out['stringcol']:
            self.assertTrue(y != 'fred')

    def test_int_search(self):
        # intcol should not contain '2'
        params = {
            'colnames': 'intcol',
            'to_replace': '2',
            'match_case': False,
            'regex': False,
            'match_entire': False,
            'replace_with': ''
        }
        out = render(self.table.copy(), params)
        self.assertTrue(out['intcol'].dtype == object)
        for y in out['intcol']:
            self.assertTrue(y != '2')

    def test_exact(self):
        # datecol[2] should be none
        params = {
            'colnames': 'datecol',
            'to_replace': '1964',
            'match_case': False,
            'regex': False,
            'match_entire': True,
            'replace_with': ''
        }
        out = render(self.table.copy(), params)
        for idx, value in enumerate(out['datecol']):
            if idx == 2:
                self.assertTrue(not value)
            else:
                self.assertTrue(value)

        # datecol[2] should be none per regex
        params = {
            'colnames': 'datecol',
            'to_replace': '^1964$',
            'match_case': False,
            'regex': True,
            'match_entire': True,
            'replace_with': ''
        }
        out = render(self.table.copy(), params)
        for idx, value in enumerate(out['datecol']):
            if idx == 2:
                self.assertTrue(not value)
            else:
                self.assertTrue(value)

if __name__ == '__main__':
    unittest.main()
