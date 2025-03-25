import ibis


def assert_ibis_all(table: ibis.Table, expr: ibis.Value | ibis.Deferred) -> bool:
    return all(table.select(expr.name("cond")).to_pandas().values.reshape(-1).tolist())
