from typing import List
from pydantic import BaseModel, Field, RootModel, field_validator
from enum import StrEnum

from .base import VersionedModel
from .inventory import InventoryItem
import brewfather_mcp.utils as utils


class YeastForm(StrEnum):
    DRY = "Dry"
    LIQUID = "Liquid"
    SLANT = "Slant"
    CULTURE = "Culture"
    SLURRY = "Slurry"


class YeastType(StrEnum):
    ALE = "Ale"
    LAGER = "Lager"
    HYBRID = "Hybrid"
    WHEAT = "Wheat"
    WINE = "Wine"
    CHAMPAGNE = "Champagne"
    OTHER = "Other"


class Flocculation(StrEnum):
    LOW = "Low"
    MEDIUM_LOW = "Medium-Low"
    MEDIUM = "Medium"
    MEDIUM_HIGH = "Medium-High"
    HIGH = "High"
    VERY_HIGH = "Very High"


class YeastUnit(StrEnum):
    PACKAGES = "packages"
    CELLS = "cells"
    PKG = "pkg"
    BILLION_CELLS = "billion cells"
    ML = "ml"
    G = "g"


class YeastBase(BaseModel):
    """
    Core yeast fields present in all contexts.
    """
    name: str
    type: YeastType | str  # Use enum but allow string for compatibility
    attenuation: float | None = None # Percentage (may be 0-100 or 0-1?)

    model_config = {
        "populate_by_name": True,
    }


class Yeast(YeastBase, InventoryItem):
    """
    Represents a yeast from inventory list context.
    """
    form: YeastForm | None = None

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "_id": "default-016efc",
                    "attenuation": 81,
                    "inventory": 0,
                    "name": "Safale American",
                    "type": "Ale",
                }
            ]
        },
    }


class YeastDetail(Yeast, VersionedModel):
    """
    Extended yeast model with all additional properties from inventory detail context.
    """
    # Laboratory and product info
    laboratory: str
    product_id: str | None = Field(alias="productId", default=None)
    lot_number: str | None = Field(alias="lotNumber", default=None)
    
    # Performance characteristics
    min_attenuation: int | None = Field(alias="minAttenuation", default=None)
    max_attenuation: int | None = Field(alias="maxAttenuation", default=None)
    min_temp: float | None = Field(alias="minTemp", default=None)
    max_temp: float | None = Field(alias="maxTemp", default=None)
    max_abv: int | None = Field(alias="maxAbv", default=None)
    age_rate: int | None = Field(alias="ageRate", default=None)
    
    # Physical characteristics
    form: YeastForm | None = None
    flocculation: Flocculation | str | None = None  # Use enum but allow string for compatibility
    cells_per_pkg: int | None = Field(alias="cellsPerPkg", default=None)
    ferments_all: bool = Field(alias="fermentsAll", default=False)

    # Usage and storage
    description: str | None = None
    unit: YeastUnit | str | None = None  # Use enum but allow string for compatibility
    amount: float | None = None
    cost_per_amount: float | None = Field(alias="costPerAmount", default=None)
    
    # Dates
    best_before_date: str | None = Field(alias="bestBeforeDate", default=None)
    manufacturing_date: str | None = Field(alias="manufacturingDate", default=None)
    
    # Documentation
    user_notes: str = Field(alias="userNotes", default="")
    
    # System fields
    hidden: bool = False

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("manufacturing_date", "best_before_date", mode="before")
    @classmethod
    def convert_timestamp_to_isodate(cls, value: int | str | None):
        if isinstance(value, int):
            return utils.convert_timestamp_to_iso8601(value)
        return value


class RecipeYeast(YeastBase):
    """Yeast in a recipe context"""
    # Recipe-specific required fields
    amount: float
    
    # Laboratory and product info
    laboratory: str = ""
    product_id: str | None = Field(alias="productId", default=None)
    form: YeastForm | None = None
    unit: YeastUnit | str | None = None  # Use enum but allow string for compatibility
    description: str | None = None
    
    # Performance characteristics
    min_attenuation: int | None = Field(alias="minAttenuation", default=None)
    max_attenuation: int | None = Field(alias="maxAttenuation", default=None)
    min_temp: float | None = Field(alias="minTemp", default=None)
    max_temp: float | None = Field(alias="maxTemp", default=None)
    max_abv: int | None = Field(alias="maxAbv", default=None)
    
    # Physical characteristics
    flocculation: Flocculation | str | None = None  # Use enum but allow string for compatibility
    ferments_all: bool = Field(alias="fermentsAll", default=False)
    
    # Dates
    best_before_date: str | None = Field(alias="bestBeforeDate", default=None)
    manufacturing_date: str | None = Field(alias="manufacturingDate", default=None)
    
    # Documentation
    user_notes: str | None = Field(alias="userNotes", default=None)
    
    # Starter information (recipe-specific)
    starter: bool | None = Field(default=None)
    starter_size: float | None = Field(alias="starterSize", default=None)
    starter_gram_extract: float | None = Field(alias="starterGramExtract", default=None)
    
    # Optional inventory link
    inventory: float | None = None
    hidden: bool = False
    
    # ID may be null for custom recipe entries  
    id: str | None = Field(alias="_id", default=None)
    
    # Parent reference for recipe inheritance
    parent: str | None = Field(alias="_parent", default=None)

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("manufacturing_date", "best_before_date", mode="before")
    @classmethod
    def convert_timestamp_to_isodate(cls, value: int | str | None):
        if isinstance(value, int):
            return utils.convert_timestamp_to_iso8601(value)
        return value


class BatchYeast(RecipeYeast):
    """Yeast in a batch context with batch-specific tracking fields"""
    
    # Batch-specific tracking fields
    display_amount: float = Field(alias="displayAmount", default=0.0)
    total_cost: float = Field(alias="totalCost", default=0.0)
    cost_per_amount: float | None = Field(alias="costPerAmount", default=None)
    not_in_recipe: bool = Field(alias="notInRecipe", default=False)
    inventory_unit: str | None = Field(alias="inventoryUnit", default=None)
    
    model_config = {
        "populate_by_name": True,
    }


class YeastList(RootModel[List[Yeast]]):
    """A collection of yeasts."""
    pass