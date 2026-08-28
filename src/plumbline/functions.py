"""Excel functions xlcalculator does not ship, registered into its function table.

Measured against 1,500 Enron workbooks (1.7M formula cells), xlcalculator alone
evaluates 93.0% of formula cells. The shortfall is concentrated in a handful of
functions, so implementing them is far cheaper than changing engines:

    INDEX      46,587 uses   ->  95.7%
    NORMINV    40,984        ->  98.1%
    VALUE       7,435        ->  98.5%
    HLOOKUP     6,563        ->  98.9%

`NORMINV` and `RAND` dominating this corpus is a fingerprint of what Enron was:
an energy trading firm running Monte Carlo risk simulations.

Importing this module registers everything. `plumbline/__init__.py` does that, so
callers get the extended registry for free.

Deliberately NOT implemented: OFFSET and INDIRECT. They construct references at
runtime, so a workbook using them has no statically knowable dependency graph.
Every analysis Plumbline performs rests on that graph, so those workbooks are
reported as unauditable rather than silently mis-analysed. See Docs/DESIGN.md §6c.
"""

from __future__ import annotations

from xlcalculator.xlfunctions import func_xltypes, xl, xlerrors


@xl.register()
@xl.validate_args
def INDEX(
    array: func_xltypes.XlArray,
    row_num: func_xltypes.XlNumber,
    column_num: func_xltypes.XlNumber = None,
) -> func_xltypes.XlAnything:
    """Return the value at a given position in a range.

    https://support.microsoft.com/en-us/office/index-function-a5dcf0dd-996d-40a4-a822-b56b061328bd

    Excel is 1-indexed. A single-row or single-column range may be addressed with
    one index, in which case that index walks the vector regardless of orientation.
    The array form (row_num or column_num of 0, returning a whole row/column) is
    not supported -- it only means anything inside an array formula, and returning
    a scalar there would be silently wrong.
    """
    rows = array.values.tolist() if hasattr(array.values, "tolist") else list(array.values)
    n_rows = len(rows)
    n_cols = len(rows[0]) if n_rows else 0
    if n_rows == 0 or n_cols == 0:
        return xlerrors.RefExcelError("INDEX received an empty range.")

    r = int(row_num)
    c = int(column_num) if column_num is not None else None

    if r == 0 or c == 0:
        return xlerrors.ValueExcelError(
            "INDEX array form (row_num or column_num of 0) is not supported."
        )

    # Vector form: one index into a single row or single column.
    if c is None:
        if n_rows == 1:
            if not 1 <= r <= n_cols:
                return xlerrors.RefExcelError(f"INDEX position {r} outside 1..{n_cols}.")
            return rows[0][r - 1]
        if n_cols == 1:
            if not 1 <= r <= n_rows:
                return xlerrors.RefExcelError(f"INDEX position {r} outside 1..{n_rows}.")
            return rows[r - 1][0]
        # Two-dimensional range with only a row index: Excel returns the whole row.
        return xlerrors.ValueExcelError(
            "INDEX over a 2-D range requires column_num."
        )

    if not 1 <= r <= n_rows:
        return xlerrors.RefExcelError(f"INDEX row {r} outside 1..{n_rows}.")
    if not 1 <= c <= n_cols:
        return xlerrors.RefExcelError(f"INDEX column {c} outside 1..{n_cols}.")
    return rows[r - 1][c - 1]


@xl.register()
@xl.validate_args
def NORMINV(
    probability: func_xltypes.XlNumber,
    mean: func_xltypes.XlNumber,
    standard_dev: func_xltypes.XlNumber,
) -> func_xltypes.XlNumber:
    """Inverse of the normal cumulative distribution.

    https://support.microsoft.com/en-us/office/norm-inv-function-54b30935-fee7-493c-bedb-2278a9db7e13

    scipy is already an xlcalculator dependency, so this costs no new install.
    """
    from scipy.stats import norm

    p = float(probability)
    sd = float(standard_dev)
    if sd <= 0:
        return xlerrors.NumExcelError("NORMINV requires standard_dev > 0.")
    if not 0 < p < 1:
        return xlerrors.NumExcelError("NORMINV requires 0 < probability < 1.")
    return float(norm.ppf(p, loc=float(mean), scale=sd))


@xl.register()
@xl.validate_args
def VALUE(text: func_xltypes.XlAnything) -> func_xltypes.XlNumber:
    """Coerce a text representation of a number to a number.

    https://support.microsoft.com/en-us/office/value-function-257d0108-07dc-437d-ae1c-bc2d3953d8c2
    """
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        return float(text)
    s = str(text).strip()
    if not s:
        return xlerrors.ValueExcelError("VALUE received empty text.")
    negative = s.startswith("(") and s.endswith(")")  # accounting notation
    if negative:
        s = s[1:-1]
    percent = s.endswith("%")
    if percent:
        s = s[:-1]
    s = s.replace(",", "").replace("$", "").strip()
    try:
        n = float(s)
    except ValueError:
        return xlerrors.ValueExcelError(f"VALUE cannot convert {text!r} to a number.")
    if percent:
        n /= 100.0
    return -n if negative else n


@xl.register()
@xl.validate_args
def HLOOKUP(
    lookup_value: func_xltypes.XlAnything,
    table_array: func_xltypes.XlArray,
    row_index_num: func_xltypes.XlNumber,
    range_lookup=False,
) -> func_xltypes.XlAnything:
    """Search the first row of a range and return a value from the row below.

    https://support.microsoft.com/en-us/office/hlookup-function-a3034eec-b719-4ba3-bb65-e1ad662ed95f

    Exact match only, mirroring xlcalculator's own VLOOKUP, which raises on
    approximate match rather than guessing.
    """
    if range_lookup:
        raise NotImplementedError("Exact match only supported at the moment.")

    rows = table_array.values.tolist() if hasattr(table_array.values, "tolist") else list(
        table_array.values
    )
    if not rows:
        return xlerrors.RefExcelError("HLOOKUP received an empty range.")

    r = int(row_index_num)
    if not 1 <= r <= len(rows):
        return xlerrors.RefExcelError(f"HLOOKUP row {r} outside 1..{len(rows)}.")

    header = rows[0]
    for col, cell in enumerate(header):
        if cell == lookup_value:
            return rows[r - 1][col]
    return xlerrors.NaExcelError("`lookup_value` not in first row of `table_array`.")


#: Functions Plumbline adds on top of xlcalculator's registry.
ADDED = ("INDEX", "NORMINV", "VALUE", "HLOOKUP")

#: Functions we deliberately refuse to evaluate, and why.
UNSUPPORTED_BY_DESIGN = {
    "OFFSET": "builds a reference at runtime; dependency graph is not statically knowable",
    "INDIRECT": "builds a reference from a string at runtime; same problem",
}
