from pathlib import Path

import pyarrow as pa
from cjwmodule.arrow.testing import assert_result_equals, make_column, make_table
from cjwmodule.arrow.types import ArrowRenderResult
from cjwmodule.spec.testing import param_factory
from cjwmodule.testing.i18n import i18n_message
from cjwmodule.types import RenderError

from replace import render_arrow_v1 as render

P = param_factory(Path(__file__).parent.parent / "replace.yaml")


def test_no_columns():
    table = make_table(make_column("A", ["a", "b"]))
    result = render(table, P())
    assert_result_equals(result, ArrowRenderResult(table))


def test_invalid_regex():
    result = render(
        make_table(make_column("A", ["a"])),
        P(colnames=["A"], to_replace="(", regex=True),
    )
    assert_result_equals(
        result,
        ArrowRenderResult(
            pa.table({}),
            [
                RenderError(
                    i18n_message("error.regex.general", {"error": "missing ): (()"}),
                )
            ],
        ),
    )


def test_replace_regex_with_invalid_escape_sequence():
    # Raised error 2020-06-17
    result = render(
        make_table(make_column("A", ["a"])),
        P(colnames=["A"], to_replace="a", regex=True, replace_with="\\s"),
    )
    assert_result_equals(
        result,
        ArrowRenderResult(
            pa.table({}),
            [
                RenderError(
                    i18n_message(
                        "error.replace_with.template",
                        {
                            "error": "Rewrite schema error: '\\' must be followed by a digit or '\\'."
                        },
                    ),
                )
            ],
        ),
    )


def test_replace_non_regex_with_invalid_escape_sequence():
    # non-regexes just replace the text
    result = render(
        make_table(make_column("A", ["a"])),
        P(colnames=["A"], to_replace="a", replace_with="\\s"),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", ["\\s"])))
    )


def test_replace_with_invalid_replacement_number():
    result = render(
        make_table(make_column("A", ["a"])),
        P(
            colnames=["A", "B"],
            to_replace="([bB])[cC]",
            regex=True,
            replace_with=r"\2 \1",
        ),
    )
    assert_result_equals(
        result,
        ArrowRenderResult(
            pa.table({}),
            [
                RenderError(
                    i18n_message(
                        "error.replace_with.template",
                        {
                            "error": "Rewrite schema requests 2 matches, but the regexp only has 1 parenthesized subexpressions."
                        },
                    )
                )
            ],
        ),
    )


def test_replace_str_with_invalid_escape_sequence():
    # Raised error 2020-06-17
    #
    # Pandas simply assumes a backslash means regex, even when you pass the
    # regex=False argument. Test that we don't do what Pandas does.
    result = render(
        make_table(make_column("A", ["a"])),
        P(colnames=["A"], to_replace="a", regex=False, replace_with=r"\0\s\t"),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", [r"\0\s\t"])))
    )


def test_replace_str_without_adding_backslash():
    # Doubling down after test_replace_str_with_invalid_escape_sequence
    result = render(
        make_table(make_column("A", ["a"])),
        P(colnames=["A"], to_replace="a", regex=False, replace_with="b c"),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", ["b c"])))
    )


def test_regex_str_case_insensitive():
    result = render(
        make_table(make_column("A", ["AaAfredaAaA", "aAaAfredaAAaaa"])),
        P(colnames=["A"], to_replace="[a]", match_case=False, regex=True),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", ["fred", "fred"])))
    )


def test_regex_str_case_sensitive():
    result = render(
        make_table(make_column("A", ["AafredaaA", "aAafredaAaaa"])),
        P(colnames=["A"], to_replace="[a]", match_case=True, regex=True),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", ["AfredA", "AfredA"])))
    )


def test_str_str_case_insensitive():
    result = render(
        make_table(make_column("A", ["AaAfredaAaA", "aAaAfredaAAaaa"])),
        P(colnames=["A"], to_replace="a", match_case=False, regex=False),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", ["fred", "fred"])))
    )


def test_str_str_case_sensitive():
    result = render(
        make_table(make_column("A", ["AafredaaA", "aAafredaAaaa"])),
        P(colnames=["A"], to_replace="a", match_case=True, regex=False),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", ["AfredA", "AfredA"])))
    )


def test_replace_nulls():
    result = render(
        make_table(make_column("A", ["foo", None, "floo", None, "few", "fu"])),
        P(
            colnames=["A"],
            to_replace="(o)",
            match_case=True,
            regex=True,
            replace_with="O\\1",
        ),
    )
    assert_result_equals(
        result,
        ArrowRenderResult(
            make_table(make_column("A", ["fOoOo", None, "flOoOo", None, "few", "fu"]))
        ),
    )


def test_match_entire_regex():
    result = render(
        make_table(make_column("A", ["x", "xa"])),
        P(
            colnames=["A"],
            to_replace="[x]*",
            replace_with="y",
            regex=True,
            match_entire=True,
        ),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", ["y", "xa"])))
    ),


def test_match_entire_search():
    result = render(
        make_table(make_column("A", ["x", "xa"])),
        P(
            colnames=["A"],
            to_replace="x",
            replace_with="y",
            regex=False,
            match_entire=True,
        ),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", ["y", "xa"])))
    )


def test_match_entire_empty_search():
    result = render(
        make_table(make_column("A", ["x", "", None])),
        P(
            colnames=["A"],
            to_replace="",
            replace_with="y",
            regex=False,
            match_entire=True,
        ),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", ["x", "y", None])))
    )


def test_match_entire_regex_empty_search():
    result = render(
        make_table(make_column("A", ["x", "", None])),
        P(
            colnames=["A"],
            to_replace="",
            replace_with="y",
            regex=True,
            match_entire=True,
        ),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", ["x", "y", None])))
    )


def test_categorical_rename_one_category():
    result = render(
        make_table(make_column("A", ["a", "b", "c", "b"], dictionary=True)),
        P(colnames=["A"], to_replace="a", replace_with="d"),
    )
    assert_result_equals(
        result,
        ArrowRenderResult(
            make_table(make_column("A", ["d", "b", "c", "b"], dictionary=True))
        ),
    )


def test_categorical_rename_many_cateogries_to_one():
    result = render(
        make_table(make_column("A", ["a", "b", "c", "d"], dictionary=True)),
        P(colnames=["A"], to_replace="[ac]", replace_with="d", regex=True),
    )
    assert_result_equals(
        result,
        ArrowRenderResult(
            make_table(make_column("A", ["d", "b", "d", "d"], dictionary=True))
        ),
    )


def test_categorical_rename_to_existing_category():
    result = render(
        make_table(make_column("A", ["a", "b", "c", "b"], dictionary=True)),
        P(colnames=["A"], to_replace="a", replace_with="c"),
    )
    assert_result_equals(
        result,
        ArrowRenderResult(
            make_table(make_column("A", ["c", "b", "c", "b"], dictionary=True))
        ),
    )


def test_categorical_do_not_replace_null():
    result = render(
        make_table(make_column("A", ["a", "b", None, "a", None], dictionary=True)),
        P(colnames=["A"], to_replace="a", replace_with="X"),
    )
    assert_result_equals(
        result,
        ArrowRenderResult(
            make_table(make_column("A", ["X", "b", None, "X", None], dictionary=True))
        ),
    )


def test_replace_crash_12774():
    # https://issues.apache.org/jira/browse/ARROW-12774
    table = make_table(make_column("A", ["a"] * 16))
    result = render(table, P(colnames=["A"], to_replace="X", replace_with="Y"))
    result.table[0].validate(full=True)
    assert_result_equals(result, ArrowRenderResult(table))


def test_replace_with_escape_sequence():
    result = render(
        make_table(make_column("A", ["aBc", "bCd"])),
        P(
            colnames=["A", "B"],
            to_replace="([bB])([cC])",
            regex=True,
            replace_with=r"\2 \1",
        ),
    )
    assert_result_equals(
        result, ArrowRenderResult(make_table(make_column("A", ["ac B", "C bd"])))
    )


def test_replace_no_chunks_dictionary():
    no_chunks = pa.chunked_array([], pa.utf8())
    table = pa.table({"A": no_chunks})
    result = render(
        table,
        P(colnames=["A"], to_replace="a", replace_with="b"),
    )
    assert result.table["A"].num_chunks == 0
