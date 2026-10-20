# Run with: uv run pytest snail_test.py -v

import pytest
from pydantic import ValidationError

from snail_schema import BlackboardEntry, EntryStatus, EntryType


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

@pytest.mark.parametrize("entry_type", [EntryType.RESULT, EntryType.VERDICT])
def test_non_root_types_without_parent_are_rejected(entry_type):
    with pytest.raises(ValidationError):
        BlackboardEntry(
            id="e005",
            type=entry_type,
            author="worker",
            model="claude-haiku-4-5",
            content="...",
        )


def test_invalid_status_is_rejected():
    with pytest.raises(ValidationError):
        BlackboardEntry(
            id="e006",
            type=EntryType.INTERPRETATION,
            author="interpreter",
            model="claude-haiku-4-5",
            content="...",
            status="not_a_real_status",
        )


def test_entry_is_immutable():
    entry = BlackboardEntry(
        id="e007",
        type=EntryType.INTERPRETATION,
        author="interpreter",
        model="claude-haiku-4-5",
        content="Summarize document X",
    )
    with pytest.raises(ValidationError):
        entry.content = "changed"
