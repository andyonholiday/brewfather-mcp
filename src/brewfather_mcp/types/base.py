from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, RootModel, Field

class Timestamp(BaseModel):
    """Represents a timestamp with seconds and nanoseconds."""

    seconds: int = Field(alias="_seconds")
    nanoseconds: int = Field(alias="_nanoseconds")

    def to_datetime(self) -> datetime:
        """Convert the timestamp to a Python datetime object."""
        return datetime.fromtimestamp(self.seconds + (self.nanoseconds / 1e9))
    
class VersionedModel(BaseModel):
    # Version tracking fields found in API responses (but not always)
    version: str | None = Field(alias="_version", default=None)
    created: Timestamp | None = Field(alias="_created", default=None)
    timestamp: Timestamp | None = Field(alias="_timestamp", default=None)
    timestamp_ms: int | None = Field(alias="_timestamp_ms", default=None)
    rev: str | None = Field(alias="_rev", default=None)

class CarbonationType(StrEnum):
    SUGAR = "Sugar"
    KEG_FORCE = "Keg (Force)"
    CO2_TABS = "CO2 Tabs"

class FgFormula(StrEnum):
    NORMAL = "normal"
    ADVANCED = "adv"

class IbuFormula(StrEnum):
    TINSETH = "tinseth"
    RAGER = "rager"
    GARETZ = "garetz"


class MashStepType(StrEnum):
    INFUSION = "Infusion"
    TEMPERATURE = "Temperature"
    DECOCTION = "Decoction"

class FermentationStepType(StrEnum):
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    TERTIARY = "Tertiary"
    CONDITIONING = "Conditioning"
    COLD_CRASH = "Cold Crash"
    CARBONATION = "Carbonation"


class TimeUnit(StrEnum):
    DAYS = "days"
    DAY = "day"
    MINUTES = "min"


class MashStep(BaseModel):
    """Single step in a mash schedule"""
    name: str | None = None
    type: MashStepType
    step_temp: float = Field(alias="stepTemp")
    step_time: int = Field(alias="stepTime")
    ramp_time: int | None = Field(alias="rampTime", default=None)
    infuse_temp: float | None = Field(alias="infuseTemp", default=None)
    infuse_amount: float | None = Field(alias="infuseAmount", default=None)
    display_step_temp: float | None = Field(alias="displayStepTemp", default=None)

class MashSchedule(BaseModel):
    """Mash schedule with multiple steps"""
    name: str
    steps: list[MashStep]

class BoilStep(BaseModel):
    """Single step in a boil schedule"""
    name: str
    time: int

class EquipmentProfile(BaseModel):
    name: str
class EquipmentProfileDetail(EquipmentProfile):
    """Equipment profile with brewing equipment settings"""
    name: str
    batch_size: float = Field(alias="batchSize")
    efficiency: float
    mash_efficiency: float = Field(alias="mashEfficiency")
    boil_size: float = Field(alias="boilSize")
    boil_time: int = Field(alias="boilTime")
    
    # Volume settings
    bottling_volume: float = Field(alias="bottlingVolume")
    fermenter_volume: float = Field(alias="fermenterVolume")
    trub_chiller_loss: float = Field(alias="trubChillerLoss")
    post_boil_kettle_vol: float = Field(alias="postBoilKettleVol")
    boil_off_per_hr: float = Field(alias="boilOffPerHr")
    
    # Mash settings
    mash_tun_dead_space: float = Field(alias="mashTunDeadSpace")
    mash_water_max: float = Field(alias="mashWaterMax")
    mash_water_volume_limit_enabled: bool = Field(alias="mashWaterVolumeLimitEnabled")
    sparge_temperature: float = Field(alias="spargeTemperature")
    grain_temperature: float = Field(alias="grainTemperature")
    ambient_temperature: float = Field(alias="ambientTemperature")
    
    # Efficiency settings
    efficiency_type: str = Field(alias="efficiencyType")
    calc_mash_efficiency: bool = Field(alias="calcMashEfficiency")
    evaporation_rate: float = Field(alias="evaporationRate")
    
    # Hop utilization
    hop_utilization: float = Field(alias="hopUtilization")
    calc_aroma_hop_utilization: bool = Field(alias="calcAromaHopUtilization")
    aroma_hop_utilization: float = Field(alias="aromaHopUtilization")
    hopstand_temperature: float = Field(alias="hopstandTemperature")
    
    # Loss estimates
    fermenter_loss: float | None = Field(alias="fermenterLoss", default=None)
    fermenter_loss_estimate: float = Field(alias="fermenterLossEstimate")
    
    # Calculation flags
    calc_boil_volume: bool = Field(alias="calcBoilVolume")
    mash_water_formula: str | None = Field(alias="mashWaterFormula", default=None)
    sparge_water_formula: str | None = Field(alias="spargeWaterFormula", default=None)

    model_config = {
        "populate_by_name": True,
    }

class FermentationStep(BaseModel):
    """Single step in a fermentation schedule"""
    type: FermentationStepType
    step_temp: float = Field(alias="stepTemp")
    step_time: int = Field(alias="stepTime")
    actual_time: int | None = Field(alias="actualTime", default=None)
    display_step_temp: float | None = Field(alias="displayStepTemp", default=None)
    display_pressure: float | None = Field(alias="displayPressure", default=None)
    pressure: float | None = None
    ramp: float | None = None

class FermentationSchedule(BaseModel):
    """Fermentation schedule with multiple steps"""
    name: str
    steps: list[FermentationStep]

    model_config = {
        "populate_by_name": True,
    }

class WaterProfile(BaseModel):
    """Water profile with mineral content and pH"""
    name: str | None = None
    type: str | None = None
    calcium: float | None = None
    magnesium: float | None = None
    sodium: float | None = None
    chloride: float | None = None
    sulfate: float | None = None
    bicarbonate: float | None = None
    ph: float | None = None
    hardness: float | None = None
    alkalinity: float | None = None
    residual_alkalinity: float | None = Field(alias="residualAlkalinity", default=None)

class WaterAdjustment(BaseModel):
    """Water adjustment amounts"""
    calcium: float = 0
    magnesium: float = 0
    sodium: float = 0
    chloride: float = 0
    sulfate: float = 0
    bicarbonate: float = 0
    volume: float
    calcium_chloride: float | None = Field(alias="calciumChloride", default=None)
    calcium_sulfate: float | None = Field(alias="calciumSulfate", default=None)
    magnesium_sulfate: float | None = Field(alias="magnesiumSulfate", default=None)
    sodium_chloride: float | None = Field(alias="sodiumChloride", default=None)
    sodium_bicarbonate: float | None = Field(alias="sodiumBicarbonate", default=None)

class WaterSettings(BaseModel):
    """Complete water profile and adjustment settings"""
    source: WaterProfile
    mash: WaterProfile
    sparge: WaterProfile
    total: WaterProfile
    mash_adjustments: WaterAdjustment = Field(alias="mashAdjustments")
    sparge_adjustments: WaterAdjustment = Field(alias="spargeAdjustments")
    total_adjustments: WaterAdjustment = Field(alias="totalAdjustments")
    enable_sparge_adjustments: bool = Field(alias="enableSpargeAdjustments")
    mash_ph: float = Field(alias="mashPh")
    acid_ph_adjustment: float = Field(alias="acidPhAdjustment")
    sparge_acid_ph_adjustment: float = Field(alias="spargeAcidPhAdjustment")

    model_config = {
        "populate_by_name": True,
    }
