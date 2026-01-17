from os import getenv as env

from celery import Celery
from celery.schedules import crontab

app = Celery(
	"coffee_tasks",
	broker=env("CELERY_BROKER_URL"),
	backend=env("CELERY_RESULT_BACKEND"),
	include=["src.tasks"],
)

app.conf.task_routes = {
	"src.tasks.handle_wtss": {"queue": "bdc.wtss"},
	"src.tasks.handle_stac": {"queue": "bdc.stac"},
	"src.tasks.wtss_cron": {"queue": "bdc.wtss"},
}

app.conf.beat_schedule = {
	"wtss_send_payload": {
		"task": "src.tasks.wtss_cron",
		"schedule": crontab(days="*/16"),  # A cada 16 dias
	}
}

app.conf.timezone = "America/Sao_Paulo"
app.conf.enable_utc = True
