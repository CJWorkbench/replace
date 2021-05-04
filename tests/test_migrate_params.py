from pathlib import Path

from cjwmodule.spec.testing import param_factory

from replace import migrate_params

P = param_factory(Path(__file__).parent.parent / "replace.yaml")


def test_v0_no_colnames():
    assert migrate_params(
        {
            "colnames": "",
            "to_replace": "x",
            "replace_with": "y",
            "match_case": False,
            "match_entire": True,
            "regex": False,
        }
    ) == P(
        colnames=[],
        to_replace="x",
        replace_with="y",
        match_case=False,
        match_entire=True,
        regex=False,
    )


def test_v0_with_colnames():
    assert migrate_params(
        {
            "colnames": "A,B",
            "to_replace": "x",
            "replace_with": "y",
            "match_case": False,
            "match_entire": True,
            "regex": False,
        }
    ) == P(
        colnames=["A", "B"],
        to_replace="x",
        replace_with="y",
        match_case=False,
        match_entire=True,
        regex=False,
    )


def test_v1():
    assert migrate_params(
        {
            "colnames": ["A", "B"],
            "to_replace": "x",
            "replace_with": "y",
            "match_case": False,
            "match_entire": True,
            "regex": False,
        }
    ) == P(
        colnames=["A", "B"],
        to_replace="x",
        replace_with="y",
        match_case=False,
        match_entire=True,
        regex=False,
    )
