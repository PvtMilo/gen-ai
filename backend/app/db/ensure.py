from sqlalchemy import Engine


def ensure_job_drive_columns(engine: Engine) -> None:
    with engine.begin() as conn:
        rows = conn.exec_driver_sql("PRAGMA table_info(jobs)").fetchall()
        if not rows:
            return

        existing = {row[1] for row in rows}
        additions = {
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
