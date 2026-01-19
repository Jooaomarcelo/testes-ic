import json
from typing import Any, Dict, Literal, Union

from pydantic import Field, TypeAdapter

from .base_model import CustomBaseModel, MongoBaseModel


class BDCBasePayload(CustomBaseModel):
	start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
	end_date: str = Field(..., description="End date in YYYY-MM-DD format")
	mode: Literal["full", "resume", "retry_failed"] = Field(
		"full",
		description="Processing mode: full, resume, or retry_failed",
	)


class WTSSCronPayload(BDCBasePayload):
	source: Literal["cron"] = "cron"
	geometry: None = Field(None, description="Geometry is resolved internally")


class WTSSApiPayload(BDCBasePayload):
	source: Literal["api"] = "api"
	geometry: Dict[str, Any] = Field(..., description="Geometry in GeoJSON format")


class WTSSAdminPayload(BDCBasePayload):
	source: Literal["admin"] = "admin"
	geometry: Dict[str, Any] | None = Field(
		..., description="Geometry in GeoJSON format"
	)


class WTSSPolygonError(CustomBaseModel):
	polygon_index: int
	geocodigo: str
	error: str


class WTSSReport(MongoBaseModel):
	job: Literal["wtss"]
	coverage: str
	start_date: str
	end_date: str
	status: Literal["success", "partial", "failed"]
	summary: Dict[str, int]
	errors: list[WTSSPolygonError]


class WTSSReportOut(WTSSReport):
	id: str = Field(..., alias="_id")


WTSSPayload = Union[WTSSCronPayload, WTSSApiPayload]

wtss_adapter = TypeAdapter(WTSSPayload)


def parse_wtss_payload(raw: bytes | dict) -> WTSSPayload:
	if isinstance(raw, bytes):
		raw = json.loads(raw)
	return wtss_adapter.validate_python(raw)


def parse_stac_payload(raw: bytes | dict) -> BDCBasePayload:
	if isinstance(raw, bytes):
		raw = json.loads(raw)
	return BDCBasePayload.model_validate(raw)
