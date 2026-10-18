"""AI Workload schema and validation."""

from pydantic import BaseModel, Field, model_validator


class Workload(BaseModel):
    """Represents an AI compute task submitted for scheduling."""

    id: str = Field(..., description="Unique workload identifier (e.g. 'job-001')")
    name: str = Field(..., description="Descriptive task name (e.g. 'LLM Fine-Tuning')")
    arrival_hour: int = Field(
        ...,
        ge=0,
        le=23,
        description="Hour of day (0-23) when the workload becomes available",
    )
    duration_hours: int = Field(
        ...,
        ge=1,
        le=24,
        description="Total hours of compute required to complete the task",
    )
    gpus_required: int = Field(
        ...,
        ge=1,
        description="Number of GPUs required concurrently by this job",
    )
    deadline_hour: int = Field(
        ...,
        ge=1,
        le=24,
        description="Hour by which the workload must be fully completed",
    )
    priority: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Workload priority from 1 (lowest) to 5 (critical)",
    )
    is_preemptible: bool = Field(
        default=False,
        description="If True, execution can be paused and split across non-consecutive hours",
    )

    @model_validator(mode="after")
    def validate_deadline_feasibility(self) -> "Workload":
        """Ensure the deadline provides at least enough time to run the job."""
        earliest_possible_finish = self.arrival_hour + self.duration_hours
        if self.deadline_hour < earliest_possible_finish:
            raise ValueError(
                f"Workload deadline ({self.deadline_hour}) is impossible! "
                f"With arrival at hour {self.arrival_hour} and duration {self.duration_hours}h, "
                f"the earliest finish hour is {earliest_possible_finish}."
            )
        return self
