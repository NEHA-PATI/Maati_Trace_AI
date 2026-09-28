import re

from services.lakehouse_writer_service.app import repository


class _Connection:
    def __init__(self):
        self.query = None
        self.parameters = None

    def execute(self, query, parameters):
        self.query = query.text
        self.parameters = parameters


class _Transaction:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, traceback):
        return False


def test_sentinel2_insert_columns_match_values(monkeypatch):
    connection = _Connection()
    monkeypatch.setattr(
        repository.engine,
        "begin",
        lambda: _Transaction(connection),
    )

    repository.upsert_sentinel2_feature_rows([{}])

    columns = re.search(
        r"INSERT INTO h3_sentinel2_features \((.*?)\)\s+VALUES",
        connection.query,
        re.DOTALL,
    ).group(1)
    values = re.search(
        r"\)\s+VALUES \((.*?)\)\s+ON CONFLICT",
        connection.query,
        re.DOTALL,
    ).group(1)

    column_names = [item.strip() for item in columns.split(",")]
    value_names = [item.strip().lstrip(":") for item in values.split(",")]

    assert column_names == value_names
    assert "spatial_level" in column_names
