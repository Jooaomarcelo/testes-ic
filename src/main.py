from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Body, Depends, FastAPI
from pydantic import BaseModel
from pymongo import AsyncMongoClient

from .core.config import settings
from .core.security.dependencies import protect
from .exceptions.error_handler import handle_exceptions
from .queues.client import PikaClient
from .routers import auth_router, coffee_router, user_router
from .utils.db import close_pool, create_pool, get_conn
from .utils.logging import setup_logging

# Configure logging
logger = setup_logging()


async def lifespan(app: FastAPI):
	"""
	Lifespan function to manage application startup and shutdown events.

	:param app: FastAPI application instance
	:type app: FastAPI
	"""
	app.state.pool = await create_pool()
	app.state.rabbitmq = PikaClient()

	scheduler = AsyncIOScheduler()
	# scheduler.add_job(wtss_cron_job, "interval", seconds=5, args=[app])

	await app.state.rabbitmq.connect()
	scheduler.start()

	yield

	await close_pool(app.state.pool)
	await app.state.rabbitmq.close()


app = FastAPI(lifespan=lifespan)

# Register exception handlers
handle_exceptions(app)

# Register routers
app.include_router(auth_router)
app.include_router(user_router, dependencies=[Depends(protect)])
app.include_router(coffee_router, dependencies=[Depends(protect)])

app.mount("/api/v1", app)


class Dummy(BaseModel):
	id: int
	name: str


@app.get("/")
async def read_root(db: AsyncMongoClient = Depends(get_conn)):
	"""
	Health check endpoint to verify the application is running.

	:return: Health status message
	:rtype: dict
	"""
	return {"status": "200", "message": "API is running", "environment": settings.env}


@app.post("/dummys/")
async def create_dummy(dummy: Dummy, db: AsyncMongoClient = Depends(get_conn)):
	"""
	Dummy endpoint to test database connection.

	:return: Dummy data
	:rtype: Dummy
	"""
	return dummy


# Test protected route
@app.get("/dummys-protected/")
async def protected_route(user=Depends(protect)):
	"""
	Protected route that requires authentication.

	:param token: JWT token for authentication
	:type token: str
	:return: Success message
	:rtype: dict
	"""
	return {"message": "You are authenticated!"}


# Test message queue
@app.post("/dummys-queue/")
async def publish_dummy(user=Depends(protect), dummy: Dummy = Body(...)):
	"""
	Protected route that requires authentication.

	:param token: JWT token for authentication
	:type token: str
	:return: Success message
	:rtype: dict
	"""
	await app.state.rabbitmq.publish(
		queue_name="bdc.wtss",
		payload={
			"id": dummy.id,
			"dummy": dummy.name,
		},
	)

	await app.state.rabbitmq.publish(
		queue_name="bdc.stac",
		payload={
			"id": dummy.id,
			"dummy": dummy.name,
		},
	)

	return {"message": "Message published to the queue!"}
