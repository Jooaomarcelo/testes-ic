from fastapi import APIRouter, Depends, Query
from pymongo.asynchronous.database import AsyncDatabase

from src.models.coffee import CoffeeYieldOut, PointTimeSeriesFetch, PointTimeSeriesOut
from src.services import coffee_service
from src.utils.db import get_conn

router = APIRouter(prefix="/coffee", tags=["coffee"])


@router.get("/yield/", response_model=list[CoffeeYieldOut])
async def get_coffee_yield(db: AsyncDatabase = Depends(get_conn)):
	"""
	Endpoint to retrieve coffee yield data.
	"""
	return await coffee_service.get_coffee_yield(db)


@router.get("/point/", response_model=PointTimeSeriesOut)
async def get_point_time_series(
	point_time_series_fetch: PointTimeSeriesFetch = Query(...),
	db: AsyncDatabase = Depends(get_conn),
):
	"""
	Endpoint to retrieve time series data for a specific point.
	"""
	return await coffee_service.get_point_time_series(db, point_time_series_fetch)
