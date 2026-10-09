import pytest

from app.utils.cancellation import (
    CancellationFlagManager,
    GracefulShutdownRequestedException,
)


def test_check_does_not_raise_before_shutdown_is_requested():
    """Verify that check() does not raise before shutdown is requested."""
    flag = CancellationFlagManager()

    flag.check()


def test_check_raises_after_shutdown_is_requested():
    """Verify that check() raises after shutdown is requested."""
    flag = CancellationFlagManager()

    flag.request_shutdown()

    with pytest.raises(GracefulShutdownRequestedException):
        flag.check()


def test_request_shutdown_is_idempotent():
    """Verify that requesting shutdown multiple times has the same effect."""
    flag = CancellationFlagManager()

    flag.request_shutdown()
    flag.request_shutdown()
    flag.request_shutdown()

    with pytest.raises(GracefulShutdownRequestedException):
        flag.check()


def test_check_consistently_raises_after_shutdown_is_requested():
    """Verify that check() continues to raise after shutdown is requested."""
    flag = CancellationFlagManager()
    flag.request_shutdown()

    with pytest.raises(GracefulShutdownRequestedException):
        flag.check()

    with pytest.raises(GracefulShutdownRequestedException):
        flag.check()


def test_cancellation_flag_instances_are_independent():
    """Verify that separate cancellation flag instances do not affect each other."""
    flag1 = CancellationFlagManager()
    flag2 = CancellationFlagManager()

    flag1.request_shutdown()

    with pytest.raises(GracefulShutdownRequestedException):
        flag1.check()

    flag2.check()
