"""Pydantic request/response schemas (the API contract)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import BusinessStatus, JobStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Auth ---------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class UserOut(ORMModel):
    id: int
    email: EmailStr
    name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- Jobs ---------------------------------------------------------------------
class JobOut(ORMModel):
    id: str
    filename: str
    status: JobStatus
    total: int
    processed: int
    failed_count: int
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    owner: UserOut


class UploadResult(BaseModel):
    job: JobOut
    ignored_columns: list[str]


# --- Businesses ---------------------------------------------------------------
class OfferMatch(BaseModel):
    id: str
    name: str
    reason: str = ""


class BusinessOut(ORMModel):
    id: int
    position: int
    status: BusinessStatus
    business_name: str
    website: str
    city: str
    country: str
    final_url: str | None
    site_status: str | None
    industry: str | None
    summary: str | None
    services: list[str] | None
    size_estimate: str | None
    gaps: list[str] | None
    offers: list[OfferMatch] | None
    priority: str | None
    outreach_angle: str | None
    confidence: str | None
    mode: str | None
    error: str | None


class BusinessPage(BaseModel):
    items: list[BusinessOut]
    total: int
