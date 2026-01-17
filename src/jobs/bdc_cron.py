from datetime import timedelta

from fastapi import FastAPI

from src.models.wtss import WTSSCronPayload
from src.utils.date_now import get_utc_now


async def wtss_cron_job(app: FastAPI):
	"""
	WTSS cron job.
	"""

	payload = WTSSCronPayload(
		start_date=(get_utc_now() - timedelta(days=7)).isoformat().split("T")[0],
		end_date=get_utc_now().isoformat().split("T")[0],
	)
	await app.state.rabbitmq.publish(
		queue_name="bdc.wtss",
		payload=payload.model_dump(),
	)
