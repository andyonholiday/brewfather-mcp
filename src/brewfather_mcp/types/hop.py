from typing import List
from pydantic import BaseModel, Field, RootModel, field_validator
from enum import StrEnum

from .base import VersionedModel, TimeUnit
from .inventory import InventoryItem
import brewfather_mcp.utils as utils


class HopUse(StrEnum):
    BOIL = "Boil"
    DRY_HOP = "Dry Hop"
    AROMA = "Aroma"
    FIRST_WORT = "First Wort"
    HOPSTAND = "Hopstand"
    MASH = "Mash"


class HopForm(StrEnum):
    PELLET = "Pellet"
    WHOLE = "Whole"
    CRYO = "Cryo"
    CO2_EXTRACT = "CO2Extract"
    PLUG = "Plug"
    LEAF = "Leaf"
    EXTRACT = "Extract"
    LIQUID = "Liquid"


class HopUsage(StrEnum):
    BITTERING = "Bittering"
    AROMA = "Aroma"
    BOTH = "Both"


class HopBase(BaseModel):
    """
    Core hop fields present in all contexts.
    """
    name: str
    type: HopForm | str  # Form type - use enum but allow string for compatibility
    alpha: float  # Alpha acid percentage

    model_config = {
        "populate_by_name": True,
    }


class Hop(HopBase, InventoryItem):
    """
    Represents a hop from inventory list context.
    """
    use: HopUse | None = None

    model_config = {
        "populate_by_name": True,
    }


class HopDetail(Hop, VersionedModel):
    """
    Extended hop model with all additional properties from inventory detail context.
    """
    # Chemical composition (oil analysis)
    beta: float | None = None
    oil: float | None = None
    myrcene: float | None = None
    caryophyllene: float | None = None
    humulene: float | None = None
    farnesene: float | None = None
    cohumulone: float | None = None
    hsi: float | None = None  # Hop Storage Index
    
    # Growing and processing info
    origin: str | None = None
    year: int | None = None
    usage: HopUsage | str | None = None  # Use enum but allow string for compatibility
    
    # Documentation
    notes: str = ""
    substitutes: str = ""
    used_in: str = Field(alias="usedIn", default="")
    user_notes: str = Field(alias="userNotes", default="")
    
    # Dates and storage
    best_before_date: str | None = Field(alias="bestBeforeDate", default=None)
    manufacturing_date: str | None = Field(alias="manufacturingDate", default=None)
    lot_number: str | None = Field(alias="lotNumber", default=None)
    
    # System fields
    hidden: bool = False
    
    # Brewing parameters (when used in recipes)
    amount: float | None = None
    time: int | None = None
    temp: float | None = None
    ibu: float = 0

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("manufacturing_date", "best_before_date", mode="before")
    @classmethod
    def convert_timestamp_to_isodate(cls, value):
        return utils.convert_timestamp_to_iso8601(value)


class RecipeHop(HopBase):
    """Hop addition in a recipe context"""
    # Recipe-specific required fields
    amount: float
    time: int | None = None
    use: HopUse | None = None
    ibu: float = 0
    
    # Common recipe fields
    beta: float | None = None
    temp: float | None = None
    origin: str | None = None
    
    # Dry hop specific fields
    actual_time: int | None = Field(alias="actualTime", default=None)
    time_unit: TimeUnit | str | None = Field(alias="timeUnit", default=None)  # Use enum but allow string for compatibility
    day: int | None = None
    
    # Chemical composition (optional in recipes)
    oil: float | None = None
    myrcene: float | None = None
    caryophyllene: float | None = None
    humulene: float | None = None
    farnesene: float | None = None
    cohumulone: float | None = None
    hsi: float | None = None
    
    # Additional info
    usage: HopUsage | str | None = None  # Use enum but allow string for compatibility
    year: int | None = None
    notes: str | None = None
    user_notes: str | None = Field(alias="userNotes", default=None)
    substitutes: str | None = None
    used_in: str | None = Field(alias="usedIn", default=None)
    
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


class BatchHop(RecipeHop):
    """Hop addition in a batch context with batch-specific tracking fields"""
    
    # Batch-specific tracking fields (always present)
    display_amount: float = Field(alias="displayAmount", default=0.0)
    total_cost: float = Field(alias="totalCost", default=0.0)
    cost_per_amount: float | None = Field(alias="costPerAmount", default=None)
    not_in_recipe: bool = Field(alias="notInRecipe", default=False)
    removed_from_inventory: bool = Field(alias="removedFromInventory", default=False)
    removed_amount: float = Field(alias="removedAmount", default=0.0)
    checked: bool = False

    model_config = {
        "populate_by_name": True,
    }


class HopList(RootModel[List[Hop]]):
    """A collection of hops."""
    pass