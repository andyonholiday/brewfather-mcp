from typing import List
from pydantic import BaseModel, Field, RootModel, field_validator
from enum import StrEnum

from .base import VersionedModel
from .inventory import InventoryItem
import brewfather_mcp.utils as utils

class MiscUse(StrEnum):
    MASH = "Mash"
    BOIL = "Boil"
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    BOTTLING = "Bottling"
    SPARGE = "Sparge"
    FLAMEOUT = "Flameout"
    STEEP = "Steep"


class MiscType(StrEnum):
    WATER_AGENT = "Water Agent"
    FINING = "Fining"
    OTHER = "Other"
    SPICE = "Spice"
    HERB = "Herb"
    FLAVOR = "Flavor"


class MiscBase(BaseModel):
    """
    Core misc fields present in all contexts.
    """
    name: str
    type: MiscType | str | None = None

    model_config = {
        "populate_by_name": True,
    }


class Misc(MiscBase, InventoryItem):
    """
    Represents a misc item from inventory list context.
    """
    use: MiscUse | None = None
    notes: str | None = None

    model_config = {
        "populate_by_name": True,
    }


class MiscDetail(Misc, VersionedModel):
    """
    Extended misc model with all additional properties from inventory detail context.
    """
    # Usage parameters
    use: MiscUse | None = None
    time: int | None = None
    time_is_days: bool = Field(alias="timeIsDays", default=False)
    amount_per_l: float | None = Field(alias="amountPerL", default=None)
    concentration: float | None = None
    
    # Water chemistry
    water_adjustment: bool = Field(alias="waterAdjustment", default=False)
    
    # Documentation
    use_for: str | None = Field(alias="useFor", default=None)
    substitutes: str | None = None
    user_notes: str | None = Field(alias="userNotes", default=None)
    
    # Dates
    best_before_date: str | None = Field(alias="bestBeforeDate", default=None)
    manufacturing_date: str | None = Field(alias="manufacturingDate", default=None)
    
    # System fields
    hidden: bool = False
    
    # Units and measurements
    unit: str | None = None

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("manufacturing_date", "best_before_date", mode="before")
    @classmethod
    def convert_timestamp_to_isodate(cls, value):
        return utils.convert_timestamp_to_iso8601(value)


class RecipeMisc(MiscBase):
    """Miscellaneous ingredient in a recipe context"""
    # Recipe-specific required fields
    amount: float
    use: MiscUse
    unit: str | None = None
    
    # Timing
    time: int | None = None
    time_is_days: bool = Field(alias="timeIsDays", default=False)
    
    # Measurements
    amount_per_l: float | None = Field(alias="amountPerL", default=None)
    concentration: float | None = None
    
    # Water chemistry
    water_adjustment: bool = Field(alias="waterAdjustment", default=False)
    
    # Documentation
    use_for: str | None = Field(alias="useFor", default=None)
    notes: str | None = None
    substitutes: str | None = None
    user_notes: str | None = Field(alias="userNotes", default=None)
    
    # Dates
    best_before_date: str | None = Field(alias="bestBeforeDate", default=None)
    manufacturing_date: str | None = Field(alias="manufacturingDate", default=None)
    
    # Optional inventory link
    inventory: float | None = None
    hidden: bool = False
    
    # ID may be null for custom recipe entries
    id: str | None = Field(alias="_id", default=None)

    model_config = {
        "populate_by_name": True,
    }


class BatchMisc(RecipeMisc):
    """Miscellaneous ingredient in a batch context with batch-specific tracking fields"""
    
    # Batch-specific tracking fields
    display_amount: float = Field(alias="displayAmount", default=0.0)
    total_cost: float = Field(alias="totalCost", default=0.0)
    cost_per_amount: float | None = Field(alias="costPerAmount", default=None)
    not_in_recipe: bool = Field(alias="notInRecipe", default=False)
    inventory_unit: str | None = Field(alias="inventoryUnit", default=None)

    model_config = {
        "populate_by_name": True,
    }


class MiscList(RootModel[List[Misc]]):
    """A collection of miscellaneous items."""
    pass