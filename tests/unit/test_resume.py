from app.utils.resume import ResumeManager


def test_resume_manager_is_inactive_when_saved_position_is_none():
    """Verify that resume is inactive when no saved position is provided."""
    resume_manager = ResumeManager(None)

    assert resume_manager.is_resuming() is False


def test_resume_manager_is_active_when_saved_position_exists():
    """Verify that resume is active when saved position is provided."""
    resume_manager = ResumeManager({"area_code": "0", "page_num": 1, "row_index": 5})

    assert resume_manager.is_resuming() is True


def test_resume_manager_stop_resuming_turns_off_resume_and_clears_state():
    """Verify that stop_resuming turns off resume and clears remaining state."""
    resume_manager = ResumeManager({"area_code": "0", "page_num": 1, "row_index": 5})

    resume_manager.stop_resuming()

    assert resume_manager.is_resuming() is False
    assert resume_manager.get_saved_value("area_code") is None
    assert resume_manager.get_saved_value("page_num") is None
    assert resume_manager.get_saved_value("row_index") is None


def test_resume_manager_get_saved_value_returns_checkpoint_value():
    """Verify that get_saved_value returns the saved checkpoint value."""
    resume_manager = ResumeManager({"area_code": "0", "page_num": 1, "row_index": 5})

    assert resume_manager.get_saved_value("page_num") == 1
    assert resume_manager.get_saved_value("row_index") == 5
    assert resume_manager.get_saved_value("area_code") == "0"


def test_resume_manager_get_saved_value_returns_none_when_key_does_not_exist():
    """Verify that get_saved_value returns None when the checkpoint key does not exist."""
    resume_manager = ResumeManager({"area_code": "0", "page_num": 1})

    assert resume_manager.get_saved_value("year_index") is None


def test_continue_from_checkpoint_returns_all_values_when_resume_is_inactive():
    """Verify that continue_from_checkpoint returns all values when resume is inactive."""
    resume_manager = ResumeManager(None)

    result = list(resume_manager.continue_from_checkpoint("area_code", ["0", "1", "2"]))

    assert result == ["0", "1", "2"]


def test_continue_from_checkpoint_returns_all_values_when_dimension_key_not_in_saved_position():
    """Verify that continue_from_checkpoint returns all values when dimension key is not in saved position."""
    resume_manager = ResumeManager({"area_code": "0", "page_num": 1})

    result = list(resume_manager.continue_from_checkpoint("row_index", range(5)))

    assert result == [0, 1, 2, 3, 4]


def test_continue_from_checkpoint_skips_values_before_resume_target():
    """Verify that continue_from_checkpoint skips values before the resume target and includes the target onward."""
    resume_manager = ResumeManager({"area_code": "2", "page_num": 1, "row_index": 1})

    result = list(
        resume_manager.continue_from_checkpoint("area_code", ["0", "1", "2", "3"])
    )

    assert result == ["2", "3"]


def test_continue_from_checkpoint_returns_no_values_when_resume_target_is_not_found():
    """Verify that continue_from_checkpoint returns no values when the resume target is not found."""
    resume_manager = ResumeManager(
        {"area_code": "13361", "page_num": 1, "row_index": 1}
    )

    result = list(resume_manager.continue_from_checkpoint("area_code", ["0", "1", "2"]))

    assert result == []


def test_continue_from_checkpoint_with_integer_values():
    """Verify that continue_from_checkpoint works with integer values (like row_index)."""
    resume_manager = ResumeManager({"area_code": "1", "page_num": 10, "row_index": 5})

    result = list(resume_manager.continue_from_checkpoint("row_index", range(10)))

    assert result == [5, 6, 7, 8, 9]


def test_clear_key_removes_key_and_keeps_resuming():
    """Verify clear_key removes the specified key from the pending resume position, leaves other keys intact, and keeps resume active when keys remain."""
    resume_manager = ResumeManager({"area_code": "2", "page_num": 3, "row_index": 1})

    resume_manager.clear_key("page_num")

    assert resume_manager.get_saved_value("page_num") is None
    assert resume_manager.get_saved_value("area_code") == "2"
    assert resume_manager.get_saved_value("row_index") == 1
    assert resume_manager.is_resuming() is True


def test_clear_key_stops_resuming_when_last_key_is_removed():
    """Verify that clear_key deactivates resume logic when the last key is removed."""
    resume_manager = ResumeManager({"page_num": 3})

    resume_manager.clear_key("page_num")

    assert resume_manager.is_resuming() is False
