from src.data.migrations.migrate import _sanitize_dsn_for_logs


def test_sanitize_dsn_for_logs_hides_password():
    # Arrange
    dsn = "mysql+pymysql://user:super-secret@example.com/database"

    # Act
    sanitized = _sanitize_dsn_for_logs(dsn)

    # Assert
    assert "super-secret" not in sanitized
    assert "***" in sanitized
