"""Base models module for the entire application."""

from datetime import datetime
from decimal import Decimal

from bson import ObjectId
from pydantic import BaseModel, ConfigDict


class CustomBaseModel(BaseModel):
    """Custom base model with default Pydantic configurations."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            Decimal: float,
            ObjectId: str,
        },
    )


class MongoBaseModel(CustomBaseModel):
    """Base model for MongoDB documents."""

    created_at: datetime
    updated_at: datetime
