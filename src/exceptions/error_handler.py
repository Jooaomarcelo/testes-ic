"""Application exception and error handling module."""

import logging
import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.config import settings
from src.utils.app_error import AppError

logger = logging.getLogger("error_controller")


def send_error_dev(exc: AppError) -> JSONResponse:
    """Send detailed error response in development environment.

    :param exc: Application exception
    :type exc: AppError
    :return: JSON response with error details
    :rtype: JSONResponse
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {
                "status": exc.status,
                "message": exc.message,
                "error": str(exc),
                "stack_trace": traceback.format_exc(),
            }
        ),
    )


def send_error_prod(exc: AppError) -> JSONResponse:
    """Send sanitized error response in production environment.

    :param exc: Application exception
    :type exc: AppError
    :return: JSON response with sanitized error
    :rtype: JSONResponse
    """
    if exc.is_operational:
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(
                {
                    "status": exc.status,
                    "message": exc.message,
                }
            ),
        )
    else:
        logger.error(f"Unexpected error: {exc}")
        return JSONResponse(
            status_code=500,
            content=jsonable_encoder(
                {
                    "status": "error",
                    "message": "An unexpected error occurred. Please try again later.",
                }
            ),
        )


def handle_exceptions(app: FastAPI):
    """Register exception handlers with the FastAPI application.

    :param app: FastAPI application instance
    :type app: FastAPI
    """

    @app.exception_handler(AppError)
    async def app_error_controller(request: Request, exc: Exception):
        """
        Controller to handle application-specific errors.

        :param request: Incoming request object
        :type request: Request
        :param exc: Application error exception
        :type exc: Exception
        :return: JSON response with error details
        :rtype: JSONResponse
        """
        app_error = AppError(
            status_code=getattr(exc, "status_code", 500),
            message=getattr(exc, "message", "An unexpected error occurred."),
        )
        logger.error(str(app_error))

        if settings.env == "development":
            return send_error_dev(app_error)
        else:
            return send_error_prod(app_error)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_controller(
        request: Request, exc: HTTPException | StarletteHTTPException
    ):
        """
        Controller to handle HTTP exceptions.

        :param request: Incoming request object
        :type request: Request
        :param exc: HTTP exception
        :type exc: Exception
        :return: JSON response with error details
        :rtype: JSONResponse
        """
        app_error = AppError(
            status_code=getattr(exc, "status_code", 500),
            message=getattr(exc, "detail", "An HTTP error occurred."),
        )

        if settings.env == "development":
            return send_error_dev(app_error)
        else:
            return send_error_prod(app_error)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_controller(
        request: Request, exc: RequestValidationError
    ):
        """
        Controller to handle validation exceptions.

        :param request: Incoming request object
        :type request: Request
        :param exc: Validation exception
        :type exc: Exception
        :return: JSON response with error details
        :rtype: JSONResponse
        """
        print(await request.body())
        messages = [f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()]

        message = "Validation error: " + "; ".join(messages)

        app_error = AppError(
            status_code=getattr(exc, "status_code", 422),
            message=message,
        )

        if settings.env == "development":
            return send_error_dev(app_error)
        else:
            return send_error_prod(app_error)
