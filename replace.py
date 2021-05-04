import pyarrow as pa
import pyarrow.compute
import re2
from cjwmodule import i18n
from cjwmodule.arrow.types import ArrowRenderResult
from cjwmodule.types import RenderError


def _process_chunked_array(
    chunked_array: pa.ChunkedArray, pattern: str, replacement: str
) -> pa.ChunkedArray:
    if not len(chunked_array):
        return chunked_array
    if pa.types.is_dictionary(chunked_array.chunks[0].type):
        return _process_nonempty_dictionary(chunked_array, pattern, replacement)
    else:
        return _process_nonempty_utf8(chunked_array, pattern, replacement)


def _process_nonempty_dictionary(
    chunked_array: pa.ChunkedArray, pattern: str, replacement: str
) -> pa.ChunkedArray:
    # Assume all chunks have the same dictionary (Workbench guarantees it)
    dictionary = chunked_array.chunks[0].dictionary
    mapping = _process_array(dictionary, pattern, replacement).dictionary_encode()
    chunks = [
        pa.DictionaryArray.from_arrays(
            mapping.indices.take(chunk.indices), mapping.dictionary
        )
        for chunk in chunked_array.chunks
    ]
    return pa.chunked_array(chunks, chunks[0].type)


def _process_nonempty_utf8(
    chunked_array: pa.ChunkedArray, pattern: str, replacement: str
) -> pa.ChunkedArray:
    chunks = [
        _process_array(chunk, pattern, replacement) for chunk in chunked_array.chunks
    ]
    return pa.chunked_array(chunks, chunks[0].type)


def _process_array(
    array: pa.StringArray, pattern: str, replacement: str
) -> pa.StringArray:
    return pa.compute.replace_substring_regex(
        array, pattern=pattern, replacement=replacement
    )


def build_pattern(
    *, to_replace: str, regex: bool, match_case: bool, match_entire: bool
) -> str:
    pattern = to_replace
    if not regex:
        pattern = re2.escape(pattern)
    if match_entire:
        pattern = "\\A" + pattern + "\\z"
    if not match_case:
        pattern = "(?i)" + pattern
    return pattern


def build_replacement(*, replace_with: str, regex: bool):
    if regex:
        return replace_with
    else:
        return replace_with.replace("\\", "\\\\")


def render_arrow_v1(table, params, **kwargs):
    if params["regex"]:
        # Validate regex.
        #
        # Error 1: it's an invalid regex
        try:
            pa.compute.replace_substring_regex(
                pa.array([""]), pattern=params["to_replace"], replacement=""
            )
        except pa.ArrowInvalid as err:
            return ArrowRenderResult(
                pa.table({}),
                errors=[
                    RenderError(
                        i18n.trans(
                            "error.regex.general",
                            "Invalid regular expression: {error}",
                            {"error": str(err)[len("Invalid regular expression: ") :]},
                        )
                    )
                ],
            )
        # Error 2: the replace_with string has invalid references
        #
        # We test by replacing in any old pattern
        try:
            pa.compute.replace_substring_regex(
                pa.array([""]),
                pattern=params["to_replace"],
                replacement=params["replace_with"],
            )
        except pa.ArrowInvalid as err:
            return ArrowRenderResult(
                pa.table({}),
                errors=[
                    RenderError(
                        i18n.trans(
                            "error.replace_with.template",
                            "Invalid replacement: {error}",
                            {"error": str(err)[len("Invalid replacement string: ") :]},
                        )
                    )
                ],
            )

    pattern = build_pattern(
        to_replace=params["to_replace"],
        regex=params["regex"],
        match_case=params["match_case"],
        match_entire=params["match_entire"],
    )
    replacement = build_replacement(
        replace_with=params["replace_with"], regex=params["regex"]
    )

    colnames_set = frozenset(params["colnames"])
    to_process = [
        (i, colname)
        for i, colname in enumerate(table.column_names)
        if colname in colnames_set
    ]
    for i, colname in to_process:
        table = table.set_column(
            i, colname, _process_chunked_array(table.columns[i], pattern, replacement)
        )

    return ArrowRenderResult(table)


def _migrate_params_v0_to_v1(params):
    """v0: colnames is comma-separated str. v1: colnames is List[str]."""
    return {**params, "colnames": [c for c in params["colnames"].split(",") if c]}


def migrate_params(params):
    if isinstance(params["colnames"], str):
        params = _migrate_params_v0_to_v1(params)
    return params
