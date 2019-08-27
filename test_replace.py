import unittest
from typing import Any, Dict
import pandas as pd
from pandas.testing import assert_frame_equal
import numpy as np
from replace import migrate_params, render


class MigrateParamsTest(unittest.TestCase):
    def test_v0_no_colnames(self):
        self.assertEqual(
            migrate_params(
                {
                    "colnames": "",
                    "to_replace": "x",
                    "replace_with": "y",
                    "match_case": False,
                    "match_entire": True,
                    "regex": False,
                }
            ),
            {
                "colnames": [],
                "to_replace": "x",
                "replace_with": "y",
                "match_case": False,
                "match_entire": True,
                "regex": False,
            },
        )

    def test_v0_with_colnames(self):
        self.assertEqual(
            migrate_params(
                {
                    "colnames": "A,B",
                    "to_replace": "x",
                    "replace_with": "y",
                    "match_case": False,
                    "match_entire": True,
                    "regex": False,
                }
            ),
            {
                "colnames": ["A", "B"],
                "to_replace": "x",
                "replace_with": "y",
                "match_case": False,
                "match_entire": True,
                "regex": False,
            },
        )

    def test_v1(self):
        self.assertEqual(
            migrate_params(
                {
                    "colnames": ["A", "B"],
                    "to_replace": "x",
                    "replace_with": "y",
                    "match_case": False,
                    "match_entire": True,
                    "regex": False,
                }
            ),
            {
                "colnames": ["A", "B"],
                "to_replace": "x",
                "replace_with": "y",
                "match_case": False,
                "match_entire": True,
                "regex": False,
            },
        )


def P(
    colnames: str = "",
    to_replace: str = "",
    replace_with: str = "",
    match_case: bool = False,
    match_entire: bool = False,
    regex: bool = False,
) -> Dict[str, Any]:
    return {
        "colnames": colnames,
        "to_replace": to_replace,
        "replace_with": replace_with,
        "match_case": match_case,
        "match_entire": match_entire,
        "regex": regex,
    }


class RenderTest(unittest.TestCase):
    def test_NOP(self):
        table = pd.DataFrame({"A": ["a", "b"]})
        result = render(table, P())
        assert_frame_equal(result, pd.DataFrame({"A": ["a", "b"]}))

    def test_invalid_regex(self):
        result = render(
            pd.DataFrame({"A": ["a"]}), P(colnames=["A"], to_replace="(", regex=True)
        )
        self.assertEqual(
            result,
            (
                "Invalid regular expression: missing ), "
                "unterminated subpattern at position 0"
            ),
        )

    def test_regex_str_case_insensitive(self):
        table = pd.DataFrame({"A": ["AaAfredaAaA", "aAaAfredaAAaaa"]})
        result = render(
            table, P(colnames=["A"], to_replace="[a]", match_case=False, regex=True)
        )
        assert_frame_equal(result, pd.DataFrame({"A": ["fred", "fred"]}))

    def test_regex_str_case_sensitive(self):
        table = pd.DataFrame({"A": ["AafredaaA", "aAafredaAaaa"]})
        result = render(
            table, P(colnames=["A"], to_replace="[a]", match_case=True, regex=True)
        )
        assert_frame_equal(result, pd.DataFrame({"A": ["AfredA", "AfredA"]}))

    def test_str_str_case_insensitive(self):
        table = pd.DataFrame({"A": ["AaAfredaAaA", "aAaAfredaAAaaa"]})
        result = render(
            table, P(colnames=["A"], to_replace="a", match_case=False, regex=False)
        )
        assert_frame_equal(result, pd.DataFrame({"A": ["fred", "fred"]}))

    def test_str_str_case_sensitive(self):
        table = pd.DataFrame({"A": ["AafredaaA", "aAafredaAaaa"]})
        result = render(
            table, P(colnames=["A"], to_replace="a", match_case=True, regex=False)
        )
        assert_frame_equal(result, pd.DataFrame({"A": ["AfredA", "AfredA"]}))

    def test_match_entire_regex(self):
        table = pd.DataFrame({"A": ["x", "xa"]})
        result = render(
            table,
            P(
                colnames=["A"],
                to_replace="[x]*",
                replace_with="y",
                regex=True,
                match_entire=True,
            ),
        )
        assert_frame_equal(result, pd.DataFrame({"A": ["y", "xa"]}))

    def test_match_entire_search(self):
        table = pd.DataFrame({"A": ["x", "xa"]})
        result = render(
            table,
            P(
                colnames=["A"],
                to_replace="x",
                replace_with="y",
                regex=False,
                match_entire=True,
            ),
        )
        assert_frame_equal(result, pd.DataFrame({"A": ["y", "xa"]}))

    def test_categorical_rename_one_category(self):
        table = pd.DataFrame({"A": ["a", "b", "c", "b"]}, dtype="category")
        result = render(table, P(colnames=["A"], to_replace="a", replace_with="d"))
        assert_frame_equal(
            result, pd.DataFrame({"A": ["d", "b", "c", "b"]}, dtype="category")
        )

    def test_categorical_rename_many_cateogries_to_one(self):
        table = pd.DataFrame({"A": ["a", "b", "c", "b"]}, dtype="category")
        result = render(
            table, P(colnames=["A"], to_replace="[ac]", replace_with="d", regex=True)
        )
        assert_frame_equal(
            result, pd.DataFrame({"A": ["d", "b", "d", "b"]}, dtype="category")
        )

    def test_categorical_rename_to_existing_category(self):
        table = pd.DataFrame({"A": ["a", "b", "c", "b"]}, dtype="category")
        result = render(table, P(colnames=["A"], to_replace="a", replace_with="c"))
        assert_frame_equal(
            result, pd.DataFrame({"A": ["c", "b", "c", "b"]}, dtype="category")
        )


if __name__ == "__main__":
    unittest.main()
