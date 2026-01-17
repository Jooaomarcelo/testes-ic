import json
from typing import Any, Dict, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter


class BDCBasePayload(BaseModel):
	start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
	end_date: str = Field(..., description="End date in YYYY-MM-DD format")


class WTSSCronPayload(BDCBasePayload):
	source: Literal["cron"] = "cron"
	geometry: None = Field(None, description="Geometry is resolved internally")


class WTSSUserPayload(BDCBasePayload):
	source: Literal["user"] = "user"
	geometry: Dict[str, Any] = Field(..., description="Geometry in GeoJSON format")


WTSSPayload = Union[WTSSCronPayload, WTSSUserPayload]

wtss_adapter = TypeAdapter(WTSSPayload)


def parse_wtss_payload(raw: bytes | dict) -> WTSSPayload:
	if isinstance(raw, bytes):
		raw = json.loads(raw)
	return wtss_adapter.validate_python(raw)
