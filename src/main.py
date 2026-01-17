from fastapi import Body, Depends, FastAPI
from pydantic import BaseModel
from pymongo import AsyncMongoClient

from .core.config import settings
from .core.security.dependencies import protect
from .exceptions.error_handler import handle_exceptions
from .routers import auth_router, coffee_router, user_router
from .tasks import handle_stac, handle_wtss
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

	yield

	await close_pool(app.state.pool)


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
async def publish_dummy(dummy: Dummy = Body(...)):
	"""
	Test endpoint to publish a dummy task to the message queue.

	:param dummy: Dummy data to be processed
	:type dummy: Dummy
	:return: Success message
	:rtype: dict
	"""
	handle_stac.delay({"id": dummy.id, "name": dummy.name})
	handle_wtss.delay(
		{
			"source": "user",
			"start_date": "2025-01-01",
			"end_date": "2025-01-05",
			"geometry": {
				"type": "FeatureCollection",
				"features": [
					{
						"type": "Feature",
						"properties": {"CD_MUN": "3108008"},
						"geometry": {
							"coordinates": [
								[
									[-44.80381857521476, -21.014497213157384],
									[-44.80219055282478, -21.01455079380142],
									[-44.802310567295876, -21.014302374291034],
									[-44.80210706449731, -21.014239051604207],
									[-44.80196095992366, -21.0138834698662],
									[-44.80198183200574, -21.013678888207835],
									[-44.80272279091429, -21.01344020925164],
									[-44.80369856074367, -21.01425853551069],
									[-44.80381857521476, -21.014497213157384],
								]
							],
							"type": "Polygon",
						},
					}
				],
			},
		}
	)
