from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

ValueType = Literal["boolean", "string"]


class FlagInput(BaseModel):
    """User-supplied fields for creating or updating a flag."""

    key: str = Field(min_length=1, max_length=128)
    description: str = ""
    environment: str | None = Field(
        default=None,
        description="Environment this flag applies to. None means all environments.",
    )
    user_id: str | None = Field(
        default=None,
        description="User this flag applies to. None means all users.",
    )
    starts_at: datetime | None = Field(
        default=None,
        description="When the flag becomes active. None means no lower bound.",
    )
    ends_at: datetime | None = Field(
        default=None,
        description="When the flag stops being active. None means no upper bound.",
    )
    value_type: ValueType = "boolean"
    boolean_value: bool | None = None
    string_value: str | None = None

    @model_validator(mode="after")
    def _check_value_payload(self) -> "FlagInput":
        if self.value_type == "boolean":
            if self.boolean_value is None:
                raise ValueError("boolean flags require boolean_value")
            if self.string_value is not None:
                raise ValueError("boolean flags must not set string_value")
        else:
            if self.string_value is None:
                raise ValueError("string flags require string_value")
            if self.boolean_value is not None:
                raise ValueError("string flags must not set boolean_value")
        if (
            self.starts_at is not None
            and self.ends_at is not None
            and self.ends_at <= self.starts_at
        ):
            raise ValueError("ends_at must be after starts_at")
        return self


class Flag(FlagInput):
    """A persisted flag, with its server-assigned identity."""

    id: UUID = Field(default_factory=uuid4)


class EvaluationContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    environment: str | None = None
    user_id: str | None = None


class Evaluation(BaseModel):
    key: str
    value_type: ValueType
    value: bool | str
    matched_flag_id: UUID
