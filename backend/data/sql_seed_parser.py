"""Minimal parser for the INSERT statements in ``supabase/seed.sql``.

Why this exists: the demo must run with ZERO external setup ($0, no keys). The
same ``seed.sql`` that Supabase executes is parsed here into memory, so there is
exactly ONE source of seed truth — no hand-maintained JSON fixture that can
drift away from the SQL.
"""
import json
import re
from typing import Any, Dict, List, Optional

# Columns that hold a Postgres TEXT[] literal ('{}' / '{"A", "B"}').
ARRAY_COLUMNS = {"parent_ids", "compliance_tags", "compliance_clearance"}
# Columns that hold JSONB.
JSON_COLUMNS = {"config"}

_INSERT_RE = re.compile(
    r"INSERT\s+INTO\s+(\w+)\s*\(([^)]*)\)\s*VALUES", re.IGNORECASE
)


def _strip_comments(sql: str) -> str:
    """Remove ``--`` comments without touching text inside string literals."""
    out: List[str] = []
    in_string = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        if in_string:
            out.append(ch)
            if ch == "'":
                # '' is an escaped quote, not a terminator.
                if i + 1 < len(sql) and sql[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                in_string = False
            i += 1
            continue
        if ch == "'":
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "-" and sql.startswith("--", i):
            while i < len(sql) and sql[i] != "\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _split_top_level(body: str, sep: str = ",") -> List[str]:
    """Split on ``sep`` at paren-depth 0, ignoring separators inside strings."""
    parts: List[str] = []
    buf: List[str] = []
    depth = 0
    in_string = False
    i = 0
    while i < len(body):
        ch = body[i]
        if in_string:
            buf.append(ch)
            if ch == "'":
                if i + 1 < len(body) and body[i + 1] == "'":
                    buf.append("'")
                    i += 2
                    continue
                in_string = False
            i += 1
            continue
        if ch == "'":
            in_string = True
            buf.append(ch)
        elif ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            buf.append(ch)
        elif ch == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    if "".join(buf).strip():
        parts.append("".join(buf))
    return parts


def _parse_pg_array(literal: str) -> List[str]:
    inner = literal.strip()
    if inner.startswith("{") and inner.endswith("}"):
        inner = inner[1:-1]
    inner = inner.strip()
    if not inner:
        return []
    items: List[str] = []
    for raw in _split_top_level(inner):
        item = raw.strip()
        if item.startswith('"') and item.endswith('"'):
            item = item[1:-1]
        items.append(item)
    return items


def _parse_value(raw: str, column: str) -> Any:
    token = raw.strip()
    if token.upper() == "NULL":
        return None
    if token.startswith("'"):
        # Strip the outer quotes and unescape doubled quotes.
        text = token[1:-1].replace("''", "'")
        if column in ARRAY_COLUMNS:
            return _parse_pg_array(text)
        if column in JSON_COLUMNS:
            return json.loads(text)
        return text
    if token.upper() in ("TRUE", "FALSE"):
        return token.upper() == "TRUE"
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        return token


def parse_seed(sql_text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Return ``{table_name: [row_dict, ...]}`` for every INSERT in the file."""
    sql = _strip_comments(sql_text)
    tables: Dict[str, List[Dict[str, Any]]] = {}

    for match in _INSERT_RE.finditer(sql):
        table = match.group(1)
        columns = [c.strip() for c in match.group(2).split(",")]
        # Walk forward from the end of "VALUES" to the statement-terminating ';'
        # that sits at paren depth 0 and outside any string literal.
        i = match.end()
        depth = 0
        in_string = False
        start = i
        while i < len(sql):
            ch = sql[i]
            if in_string:
                if ch == "'":
                    if i + 1 < len(sql) and sql[i + 1] == "'":
                        i += 2
                        continue
                    in_string = False
            elif ch == "'":
                in_string = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == ";" and depth == 0:
                break
            i += 1
        body = sql[start:i]

        rows = tables.setdefault(table, [])
        for tuple_text in _split_top_level(body):
            tuple_text = tuple_text.strip()
            if not tuple_text.startswith("("):
                continue
            values = _split_top_level(tuple_text[1:-1])
            if len(values) != len(columns):
                raise ValueError(
                    "seed.sql: {} column/value mismatch ({} vs {}) near {!r}".format(
                        table, len(columns), len(values), tuple_text[:60]
                    )
                )
            rows.append(
                {col: _parse_value(val, col) for col, val in zip(columns, values)}
            )
    return tables


def load_seed_file(path: str) -> Dict[str, List[Dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as handle:
        return parse_seed(handle.read())
