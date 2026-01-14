from typing import Any, List

from bson import ObjectId
from pydantic import ConfigDict, Field

from src.models.base_model import CustomBaseModel


class CoffeeYield(CustomBaseModel):
	"""Represents a single coffee yield document from 'producao' collection."""

	geocodigo: str
	municipio: str
	producao: List[dict[str, Any]]


class CoffeeYieldOut(CoffeeYield):
	"""Coffee yield output data model."""

	id: ObjectId = Field(..., alias="_id")

	model_config = ConfigDict(
		arbitrary_types_allowed=True,
	)


class PointTimeSeries(CustomBaseModel):
	"""Represents a single point time series document from 'cafe' collection."""

	geocodigo: str
	metadata: dict[str, Any]
	timeseries: List[dict[str, Any]]


class PointTimeSeriesFetch(CustomBaseModel):
	"""Point time series input data model."""

	lat: float
	lng: float
	max_distance: int = 10


class PointTimeSeriesOut(PointTimeSeries):
	"""Point time series output data model."""

	id: ObjectId = Field(..., alias="_id")

	model_config = ConfigDict(
		arbitrary_types_allowed=True,
	)
