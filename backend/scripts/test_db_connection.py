from shared.db.postgres import engine

with engine.connect() as conn:
    row = conn.exec_driver_sql(
        "SELECT current_database(), PostGIS_Version();"
    ).fetchone()

    print("Connected database:", row[0])
    print("PostGIS version:", row[1])