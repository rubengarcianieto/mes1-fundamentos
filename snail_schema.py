from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EntryType(str, Enum):
    """Allowed kinds of blackboard entry."""

    INTERPRETATION = "interpretation"
    TASK = "task"
    RESULT = "result"
    VERDICT = "verdict"


class EntryStatus(str, Enum):
    """Lifecycle status of an entry."""

    PROPOSED = "proposed"
    VERIFIED = "verified"
    REJECTED = "rejected"


class BlackboardEntry(BaseModel):
    """One record written to the blackboard."""

    model_config = ConfigDict(frozen=True)
    id: str
    type: EntryType
    author: str
    model: str
    content: str
    status: EntryStatus = EntryStatus.PROPOSED
    derived_from: str | None = None  # None only for the root interpretation
    created_at: datetime = Field(default_factory=datetime.now)

    @model_validator(mode="after")
    def derived_from_required_unless_root(self):
        """Non-root entries must declare their parent."""
        if self.type != EntryType.INTERPRETATION and self.derived_from is None:
            raise ValueError(
                "derived_from is required for any entry that is not "
                "the root interpretation"
            )
        return self
