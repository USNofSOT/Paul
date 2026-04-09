from src.core.bot import _build_startup_log_fields


def test_build_startup_log_fields_only_includes_startup_details():
    fields = _build_startup_log_fields(guild_name="Test Guild")
    field_map = {field.label: field.value for field in fields}

    assert set(field_map) == {
        "Environment",
        "Guild",
        "Extensions",
        "Bot Log Channel",
    }
    assert field_map["Guild"] == "Test Guild"
