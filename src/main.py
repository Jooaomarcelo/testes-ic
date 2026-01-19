from fastapi import Depends, FastAPI
from pydantic import BaseModel
from pymongo import AsyncMongoClient

from .core.config import settings
from .core.security.dependencies import protect
from .exceptions.error_handler import handle_exceptions
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
