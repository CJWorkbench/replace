import unittest
import pandas as pd
import numpy as np
from replace import render


class TestReplace(unittest.TestCase):

    def setUp(self):
        # Test data includes:
        #  - rows of numeric and string types
        self.table = pd.DataFrame([
            ['AaAfredaAaA', 12333, 3.14, '1964-5-05', 'a'],
            ['aAaAfredaAAaaa', 5211111, 45.64, '1964-7-28 08:55', 'b'],
            ['AaAfredAaaaA', -323434, 435.00, '1964', 'c'],
            ['AAfredAA', 32331, 35331.19, '1964-2-27', 'd'],
            ['AaaAfredAaaaA', 8009823, 0.07, '1964-7-30', 'c']],
            columns=['stringcol', 'intcol', 'floatcol', 'datecol', 'catcol'])

        # Pandas should infer these types anyway, but leave nothing to chance
        self.table['stringcol'] = self.table['stringcol'].astype(str)
        self.table['intcol'] = self.table['intcol'].astype(np.int64)
        self.table['floatcol'] = self.table['floatcol'].astype(np.float64)
        self.table['datecol'] = self.table['datecol'].astype(str)
        self.table['catcol'] = self.table['catcol'].astype('category')

        self.simple_table = pd.DataFrame([
            [201, 201, '201'],
            [201, 201, '201'],
            [100, 100, '100']]
            , columns=['intcol', 'catcol', 'catcol2'])

        self.simple_table['intcol'] = self.simple_table['intcol'].astype(np.int64)
        self.simple_table['catcol'] = self.simple_table['catcol'].astype('category')
        self.simple_table['catcol2'] = self.simple_table['catcol2'].astype('category')

        self.temp_table = pd.read_csv('bin/general_10000.csv', encoding='ISO-8859-1', dtype='category')

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

            # datecol should only contain '1964'
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
        # intcol should only contain '2' and convert to string
        params = {
            'colnames': 'intcol',
            'to_replace': '[0-1|3-9|\D]',
            'match_case': False,
            'regex': True,
            'match_entire': False,
            'replace_with': ''
        }
        out = render(self.table.copy(), params)
        self.assertTrue(out['intcol'].dtype == np.int64)
        for y in out['intcol']:
            self.assertTrue(y == 2)

        # floatcol should only contain '2.'
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
        self.assertTrue(out['intcol'].dtype == np.int64)
        for y in out['intcol']:
            self.assertTrue(y != '2')

    def test_cat_search(self):
        # catcol remain category with updated index
        params = {
            'colnames': 'catcol',
            'to_replace': 'c',
            'match_case': False,
            'regex': False,
            'match_entire': False,
            'replace_with': 'e'
        }
        out = render(self.table.copy(), params)
        self.assertTrue(out['catcol'].dtype == 'category')
        self.assertTrue(set(out['catcol'].cat.categories) == set(['a', 'b', 'd', 'e']))
        self.assertEqual(out['catcol'].tolist(), ['a','b','e','d','e'])

        # catcol remain category with updated index
        params = {
            'colnames': 'catcol',
            'to_replace': '[a|c]',
            'match_case': False,
            'regex': True,
            'match_entire': False,
            'replace_with': '!'
        }
        out = render(self.table.copy(), params)
        self.assertTrue(out['catcol'].dtype == 'category')
        self.assertTrue(set(out['catcol'].cat.categories) == set(['b', 'd', '!']))
        self.assertEqual(out['catcol'].tolist(), ['!', 'b', '!', 'd', '!'])

        # catcol remain category with updated index
        params = {
            'colnames': 'catcol',
            'to_replace': 'a',
            'match_case': False,
            'regex': False,
            'match_entire': False,
            'replace_with': '99'
        }
        out = render(self.table.copy(), params)
        self.assertTrue(out['catcol'].dtype == 'category')

        # catcol drop multiple rows
        params = {
            'colnames': 'catcol',
            'to_replace': '[a|c]',
            'match_case': False,
            'regex': True,
            'match_entire': False,
            'replace_with': ''
        }
        out = render(self.table.copy(), params)
        self.assertTrue(out['catcol'].dtype == 'category')
        self.assertTrue(set(out['catcol'].cat.categories) == set(['b', 'd', '']))
        self.assertEqual(out['catcol'].tolist(), ['', 'b', '', 'd', ''])

        # catcol drop multiple rows
        params = {
            'colnames': 'datecol',
            'to_replace': '[^\w\s]',
            'match_case': False,
            'regex': True,
            'match_entire': False,
            'replace_with': ''
        }
        modified_table = self.table.copy()
        modified_table['datecol'] = modified_table['datecol'].astype('category')

        out = render(modified_table, params)
        self.assertTrue(out['datecol'].dtype == 'category')
        expected_cats = set(['1964505', '1964728 0855', '1964', '1964227', '1964730'])
        self.assertTrue(set(out['datecol'].cat.categories) == expected_cats)
        self.assertEqual(set(out['datecol'].tolist()), expected_cats)

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


    def test_multiple_coltypes(self):
        # intcol converts to string, catcol converts index to string
        params = {
            'colnames': 'intcol,catcol,catcol2',
            'to_replace': '1',
            'match_case': False,
            'regex': False,
            'match_entire': False,
            'replace_with': '!'
        }
        out = render(self.simple_table.copy(), params)
        expected = pd.DataFrame([
            ["20!", "20!", "20!"],
            ["20!", "20!", "20!"],
            ["!00", "!00", "!00"]]
            , columns=['intcol', 'catcol', 'catcol2'])

        expected['catcol'] = expected['catcol'].astype('category')
        expected['catcol2'] = expected['catcol2'].astype('category')

        self.assertTrue(out.equals(expected))

        # intcol remains int, catcol remains int index
        params = {
            'colnames': 'intcol,catcol,catcol2',
            'to_replace': '1',
            'match_case': False,
            'regex': False,
            'match_entire': False,
            'replace_with': '9'
        }
        out = render(self.simple_table.copy(), params)
        expected = pd.DataFrame([
            [209, 209, "209"],
            [209, 209, "209"],
            [900, 900, "900"]]
            , columns=['intcol', 'catcol', 'catcol2'])

        expected['intcol'] = expected['intcol'].astype(np.int64)
        expected['catcol'] = expected['catcol'].astype('category')
        expected['catcol2'] = expected['catcol2'].astype('category')

        self.assertTrue(out.equals(expected))

if __name__ == '__main__':
    unittest.main()
