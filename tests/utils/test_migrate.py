from src.data.migrations.migrate import _sanitize_dsn_for_logs


def test_sanitize_dsn_for_logs_hides_password():
    dsn = "mysql+pymysql://user:super-secret@example.com/database"

    sanitized = _sanitize_dsn_for_logs(dsn)

    assert "super-secret" not in sanitized
    assert "***" in sanitized
