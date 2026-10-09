from unittest.mock import patch

import pytest

from app.utils.runtime_guard import RuntimeGuardManager, RuntimeLimitReachedException


def test_runtime_guard_manager_initializes_with_max_seconds():
    """Verify that RuntimeGuardManager initializes with the given max_seconds."""
    with patch("time.time", return_value=1000.0):
        runtime_guard = RuntimeGuardManager(runtime_limit_seconds=300)

        assert runtime_guard.deadline == 1300.0


def test_runtime_guard_check_does_not_raise_when_within_time_limit():
    """Verify that check() does not raise exception when runtime is within limit."""
    with patch("time.time", side_effect=[1000.0, 1100.0]):
        runtime_guard = RuntimeGuardManager(runtime_limit_seconds=300)

        # Should not raise - still within limit (100 < 300)
        runtime_guard.check()


def test_runtime_guard_check_raises_when_time_limit_exceeded():
    """Verify that check() raises RuntimeLimitReachedException when limit is exceeded."""
    with patch("time.time", side_effect=[1000.0, 1400.0]):
        runtime_guard = RuntimeGuardManager(runtime_limit_seconds=300)

        # Should raise - exceeded limit (400 >= 300)
        with pytest.raises(RuntimeLimitReachedException):
            runtime_guard.check()


def test_runtime_guard_check_raises_exactly_at_time_limit():
    """Verify that check() raises exception when runtime equals the limit."""
    with patch("time.time", side_effect=[1000.0, 1300.0]):
        runtime_guard = RuntimeGuardManager(runtime_limit_seconds=300)

        # Should raise - at exact limit (300 >= 300)
        with pytest.raises(RuntimeLimitReachedException):
            runtime_guard.check()


def test_runtime_guard_check_can_be_called_multiple_times():
    """Verify that check() can be called multiple times before limit is reached."""
    with patch("time.time", side_effect=[1000.0, 1100.0, 1150.0, 1200.0]):
        runtime_guard = RuntimeGuardManager(runtime_limit_seconds=300)

        # Should be able to call multiple times without raising
        runtime_guard.check()
        runtime_guard.check()
        runtime_guard.check()


def test_runtime_limit_reached_exception_is_exception():
    """Verify that RuntimeLimitReachedException is a proper exception."""
    exception = RuntimeLimitReachedException()

    assert isinstance(exception, Exception)


def test_runtime_limit_reached_exception_can_be_caught():
    """Verify that RuntimeLimitReachedException can be caught and handled."""
    caught = False

    try:
        raise RuntimeLimitReachedException()
    except RuntimeLimitReachedException:
        caught = True

    assert caught is True


def test_runtime_guard_with_zero_max_seconds():
    """Verify that check() immediately raises with runtime_limit_seconds=0."""
    with patch("time.time", side_effect=[1000.0, 1000.0]):
        runtime_guard = RuntimeGuardManager(runtime_limit_seconds=0)

        # Should raise immediately (0 >= 0)
        with pytest.raises(RuntimeLimitReachedException):
            runtime_guard.check()
