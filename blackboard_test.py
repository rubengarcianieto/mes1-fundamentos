# Run with: uv run pytest blackboard_test.py -v

import pytest
from pydantic import ValidationError

from blackboard_schema import BlackboardEntry, EntryType, EntryStatus


def test_root_interpretation_without_parent_is_valid():
    entry = BlackboardEntry(
        id="e001",
        type=EntryType.INTERPRETATION,
        author="interpreter",
        model="claude-haiku-4-5",
        content="Summarize document X",
    )
    assert entry.derived_from is None
    assert entry.status == EntryStatus.PROPOSED


def test_task_without_parent_is_rejected():
    with pytest.raises(ValidationError):
        BlackboardEntry(
            id="e002",
            type=EntryType.TASK,
            author="decomposer",
            model="claude-haiku-4-5",
            content="Find sources",
        )


def test_task_with_parent_is_valid():
    task = BlackboardEntry(
        id="e003",
        type=EntryType.TASK,
        author="decomposer",
        model="claude-haiku-4-5",
        content="Find sources",
        derived_from="e001",
    )
    assert task.derived_from == "e001"


def test_invalid_type_is_rejected():
    with pytest.raises(ValidationError):
        BlackboardEntry(
            id="e004",
            type="not_a_real_type",
            author="interpreter",
            model="claude-haiku-4-5",
            content="...",
        )
