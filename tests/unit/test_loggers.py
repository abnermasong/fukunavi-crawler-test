from datetime import UTC, datetime

from app.utils.loggers import format_duration


def test_format_duration_zero_seconds():
    start_time = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    end_time = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)

    assert format_duration(start_time, end_time) == "00:00:00"


def test_format_duration_seconds_only():
    start_time = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    end_time = datetime(2026, 1, 1, 10, 0, 59, tzinfo=UTC)

    assert format_duration(start_time, end_time) == "00:00:59"


def test_format_duration_minutes_and_seconds():
    start_time = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    end_time = datetime(2026, 1, 1, 10, 1, 11, tzinfo=UTC)

    assert format_duration(start_time, end_time) == "00:01:11"


def test_format_duration_hours_minutes_and_seconds():
    start_time = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    end_time = datetime(2026, 1, 1, 11, 1, 11, tzinfo=UTC)

    assert format_duration(start_time, end_time) == "01:01:11"
