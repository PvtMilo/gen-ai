from sqlalchemy import Engine


def ensure_job_drive_columns(engine: Engine) -> None:
    with engine.begin() as conn:
        rows = conn.exec_driver_sql("PRAGMA table_info(jobs)").fetchall()
        if not rows:
            return

        existing = {row[1] for row in rows}
        additions = {
            "mode": "VARCHAR(20) DEFAULT 'event'",
            "overlay_image_path": "VARCHAR(255)",
            "drive_file_id": "VARCHAR(128)",
            "drive_link": "VARCHAR(500)",
            "download_link": "VARCHAR(500)",
            "qr_url": "VARCHAR(500)",
            "drive_uploaded_at": "DATETIME",
            "log_text": "TEXT",
        }

        for name, col_type in additions.items():
            if name not in existing:
                conn.exec_driver_sql(f"ALTER TABLE jobs ADD COLUMN {name} {col_type}")


def ensure_photo_sessions_theme_index(engine: Engine) -> None:
    with engine.begin() as conn:
        table = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='photo_sessions'"
        ).fetchone()
        if not table:
            return

        rows = conn.exec_driver_sql("PRAGMA index_list(photo_sessions)").fetchall()
        existing = {row[1] for row in rows}
        if "ix_photo_sessions_theme_id" in existing:
            return

        conn.exec_driver_sql("CREATE INDEX ix_photo_sessions_theme_id ON photo_sessions(theme_id)")


def ensure_themes_serial_id(engine: Engine) -> None:
    with engine.begin() as conn:
        table = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='themes'"
        ).fetchone()
        if not table:
            return

        rows = conn.exec_driver_sql("PRAGMA table_info(themes)").fetchall()
        existing = {row[1] for row in rows}

        if "serial_id" not in existing:
            conn.exec_driver_sql("ALTER TABLE themes ADD COLUMN serial_id INTEGER")

        max_serial = conn.exec_driver_sql(
            "SELECT COALESCE(MAX(serial_id), 0) FROM themes"
        ).scalar()
        next_serial = int(max_serial or 0)

        missing_rows = conn.exec_driver_sql(
            "SELECT rowid FROM themes WHERE serial_id IS NULL ORDER BY rowid ASC"
        ).fetchall()
        for row in missing_rows:
            next_serial += 1
            conn.exec_driver_sql(
                "UPDATE themes SET serial_id = ? WHERE rowid = ?",
                (next_serial, row[0]),
            )

        index_rows = conn.exec_driver_sql("PRAGMA index_list(themes)").fetchall()
        index_existing = {row[1] for row in index_rows}
        if "ix_themes_serial_id" not in index_existing:
            conn.exec_driver_sql(
                "CREATE UNIQUE INDEX ix_themes_serial_id ON themes(serial_id)"
            )
