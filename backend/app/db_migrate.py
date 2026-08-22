"""Tiny additive auto-migration for the dev SQLite database.

`Base.metadata.create_all` creates any brand-new *tables*, but it never alters an
existing table — so when a new *column* is added to a model, an older database
would break and previously had to be deleted by hand. This helper closes that
gap: on startup it compares each mapped table with the live schema and issues
`ALTER TABLE ... ADD COLUMN` for the missing columns (SQLite and Postgres both
support this). It only ever *adds* columns — it never drops or retypes — so it is
safe to run on every boot and needs no migration history.
"""
from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _literal(val: object) -> str:
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, (int, float)):
        return str(val)
    return "'" + str(val).replace("'", "''") + "'"


def auto_add_missing_columns(engine: Engine, base) -> None:
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    for table in base.metadata.sorted_tables:
        if table.name not in tables:
            continue  # a brand-new table — create_all already handles it
        existing = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name in existing:
                continue
            try:
                coltype = col.type.compile(dialect=engine.dialect)
            except Exception:
                coltype = "TEXT"
            ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {coltype}'

            default = None
            if col.default is not None and getattr(col.default, "is_scalar", False):
                default = col.default.arg
            if default is not None:
                ddl += f" DEFAULT {_literal(default)}"
                if not col.nullable:
                    ddl += " NOT NULL"
            # A NOT NULL column with no default can't be added to a populated
            # table in SQLite — add it as nullable to stay safe.

            try:
                with engine.begin() as conn:
                    conn.execute(text(ddl))
                print(f"[migrate] added column {table.name}.{col.name}")
            except Exception as exc:  # pragma: no cover - best-effort
                print(f"[migrate] skipped {table.name}.{col.name}: {exc}")
