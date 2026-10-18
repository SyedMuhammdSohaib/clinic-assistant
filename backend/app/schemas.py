"""Request bodies. Unknown fields are rejected so a typo never passes silently."""
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.clock import clinic_today

PHONE_PATTERN = r"^\+?[0-9]{9,15}$"
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

# Matches numeric(8,2) in the database.
Dose = Annotated[Decimal, Field(gt=0, lt=1_000_000, decimal_places=2)]


class In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("include a timezone, for example 2026-10-12T02:10:00+05:00")
    return value


def _not_in_future(value: datetime, minutes: int = 5) -> datetime:
    if value > datetime.now(timezone.utc) + timedelta(minutes=minutes):
        raise ValueError("cannot be in the future")
    return value


# ---------------------------------------------------------------- people

class DoctorIn(In):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(pattern=EMAIL_PATTERN, max_length=200)
    phone: str | None = Field(default=None, pattern=PHONE_PATTERN)
    clinic_name: str | None = Field(default=None, max_length=200)


class PatientIn(In):
    doctor_id: UUID
    full_name: str = Field(min_length=1, max_length=200)
    date_of_birth: date
    sex: Literal["male", "female", "other"] | None = None
    weight_kg: Decimal | None = Field(default=None, gt=0, lt=200, decimal_places=2)
    preferred_language: Literal["ur", "roman_ur", "en"] = "ur"

    @field_validator("date_of_birth")
    @classmethod
    def _dob_not_future(cls, value: date) -> date:
        if value > clinic_today():
            raise ValueError("cannot be in the future")
        return value


class GuardianIn(In):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(pattern=PHONE_PATTERN)
    relation: str | None = Field(default=None, max_length=50)
    is_primary: bool = False


# ---------------------------------------------------------------- medicines

class MedicationIn(In):
    drug_name: str = Field(min_length=1, max_length=200)
    dose_amount: Dose
    dose_unit: str = Field(min_length=1, max_length=20)
    times_per_day: int = Field(ge=1, le=12)
    dose_times: list[time] | None = None
    route: str = Field(default="oral", min_length=1, max_length=40)
    reason: str | None = Field(default=None, max_length=500)
    prescribed_by: str | None = Field(default=None, max_length=200)
    started_on: date

    @model_validator(mode="after")
    def _times_match(self):
        if self.dose_times is not None and len(self.dose_times) != self.times_per_day:
            raise ValueError("dose_times needs exactly one time for each daily dose")
        return self


class MedicationChangeIn(In):
    change_type: Literal[
        "dose_increased", "dose_decreased", "frequency_changed",
        "paused", "resumed", "stopped", "switched",
    ]
    new_dose_amount: Dose | None = None
    new_times_per_day: int | None = Field(default=None, ge=1, le=12)
    reason: str | None = Field(default=None, max_length=500)
    changed_on: date | None = None  # defaults to today in the clinic's time zone

    @model_validator(mode="after")
    def _needs_values(self):
        if self.change_type in ("dose_increased", "dose_decreased") and self.new_dose_amount is None:
            raise ValueError("new_dose_amount is required for a dose change")
        if self.change_type == "frequency_changed" and self.new_times_per_day is None:
            raise ValueError("new_times_per_day is required for a frequency change")
        return self


class DoseFields(In):
    scheduled_for: datetime
    status: Literal["taken", "late", "missed", "vomited"]
    note: str | None = Field(default=None, max_length=500)

    @field_validator("scheduled_for")
    @classmethod
    def _check_time(cls, value: datetime) -> datetime:
        return _not_in_future(_aware(value), minutes=60)


class AdherenceIn(DoseFields):
    guardian_id: UUID


class ParentDoseIn(DoseFields):
    medication_id: UUID


# ---------------------------------------------------------------- events

class SeizureFields(In):
    occurred_at: datetime
    duration_seconds: int | None = Field(default=None, ge=0, le=86_400)
    seizure_type: str | None = Field(default=None, max_length=100)
    possible_trigger: str | None = Field(default=None, max_length=200)
    fever_present: bool | None = None
    description: str | None = Field(default=None, max_length=2000)
    went_to_er: bool = False

    @field_validator("occurred_at")
    @classmethod
    def _check_time(cls, value: datetime) -> datetime:
        return _not_in_future(_aware(value))


class SeizureIn(SeizureFields):
    guardian_id: UUID


class IVInfusionIn(In):
    guardian_id: UUID
    given_on: date
    fluid_or_drug: str = Field(min_length=1, max_length=200)
    given_at: str | None = Field(default=None, max_length=200)
    duration_minutes: int | None = Field(default=None, gt=0, le=10_080)
    reason: str | None = Field(default=None, max_length=500)
    reaction_noted: bool = False
    reaction_details: str | None = Field(default=None, max_length=1000)


class HospitalVisitIn(In):
    guardian_id: UUID
    visit_type: Literal["emergency", "admission", "opd", "follow_up"]
    visited_on: date
    discharged_on: date | None = None
    facility: str | None = Field(default=None, max_length=200)
    reason: str | None = Field(default=None, max_length=500)
    discharge_summary: str | None = Field(default=None, max_length=5000)
    discharge_medicines: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _dates_in_order(self):
        if self.discharged_on is not None and self.discharged_on < self.visited_on:
            raise ValueError("discharged_on cannot be before visited_on")
        return self


class SideEffectFields(In):
    medication_id: UUID | None = None
    observed_on: date
    description: str = Field(min_length=1, max_length=500)
    severity: Literal["mild", "moderate", "severe"] | None = None

    @field_validator("observed_on")
    @classmethod
    def _not_future_day(cls, value: date) -> date:
        if value > clinic_today():
            raise ValueError("cannot be in the future")
        return value


class SideEffectIn(SideEffectFields):
    guardian_id: UUID


# ---------------------------------------------------------------- parent app

class CodeRequestIn(In):
    phone: str = Field(min_length=6, max_length=30)


class CodeVerifyIn(In):
    phone: str = Field(min_length=6, max_length=30)
    code: str = Field(pattern=r"^[0-9]{6}$")


class QuestionIn(In):
    question: str = Field(min_length=3, max_length=1000)


class AnswerIn(In):
    answer: str = Field(min_length=1, max_length=2000)


# ---------------------------------------------------------------- AI

class SeizureTextIn(In):
    text: str = Field(min_length=3, max_length=2000)


class QuestionMatchIn(In):
    question: str = Field(min_length=3, max_length=1000)


class SlipPhotoIn(In):
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]
    # About 5.5 MB of base64, i.e. a 4 MB photo. The parent app shrinks photos first.
    image_base64: str = Field(min_length=100, max_length=5_600_000)


class AllergyIn(In):
    substance: str = Field(min_length=1, max_length=200)
    reaction: str | None = Field(default=None, max_length=500)
    severity: Literal["mild", "moderate", "severe"] | None = None


# ---------------------------------------------------------------- prescription slips

class UploadIn(In):
    guardian_id: UUID
    image_url: str = Field(min_length=1, max_length=2000)
    # What the extraction step read from the photo. Stored as-is for the doctor to check.
    extracted_json: dict | None = None


class UploadConfirmIn(In):
    guardian_id: UUID


class UploadApproveIn(In):
    # Only the medicines the doctor wants added. Items that already match the
    # current list are simply left out.
    items: list[MedicationIn] = Field(default_factory=list, max_length=30)
    reviewer_note: str | None = Field(default=None, max_length=1000)


class UploadRejectIn(In):
    reviewer_note: str = Field(min_length=1, max_length=1000)


# ---------------------------------------------------------------- red-flag rules

class ThresholdCondition(In):
    kind: Literal["threshold"]
    event: Literal["seizure"]
    field: Literal["duration_seconds"]
    op: Literal[">=", ">"]
    value: int = Field(ge=1, le=86_400)


class ClusterCondition(In):
    kind: Literal["cluster"]
    event: Literal["seizure"]
    count_gte: int = Field(ge=2, le=50)
    within_hours: int = Field(ge=1, le=168)


RuleCondition = Annotated[Union[ThresholdCondition, ClusterCondition], Field(discriminator="kind")]


class RuleIn(In):
    name: str = Field(min_length=1, max_length=200)
    condition: RuleCondition
    message_ur: str = Field(min_length=1, max_length=1000)
    message_en: str = Field(min_length=1, max_length=1000)
