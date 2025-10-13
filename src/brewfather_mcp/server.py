import asyncio
import logging

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts.base import Message
from mcp.types import TextContent

from brewfather_mcp.api import BrewfatherClient, ListQueryParams
from brewfather_mcp.inventory import (
    get_fermentables_summary,
    get_hops_summary,
    get_yeast_summary,
    get_miscs_summary,
)
from brewfather_mcp.types import (
    YeastForm
)
from brewfather_mcp.types.yeast import YeastType, Flocculation
from brewfather_mcp.types.recipe import RecipeType
from brewfather_mcp.types.hop import HopUse, HopForm, HopUsage
from brewfather_mcp.types.misc import MiscUse, MiscType
from brewfather_mcp.types.fermentable import FermentableType, FermentableGrainGroup
from brewfather_mcp.types.base import MashStepType, FermentationStepType
from brewfather_mcp.formatter import format_recipe_details
from typing import Optional
from datetime import datetime


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="/tmp/application.log",  # Path to log file
    filemode="a",
)

logger = logging.getLogger(__name__)

mcp = FastMCP("BrewfatherMCP")

_ = load_dotenv()

brewfather_client = BrewfatherClient()


@mcp.prompt(
    name="suggest_beer_styles",
    description="Ask to list all the possible BJCP styles based on the inventory.",
)
async def styles_based_inventory_prompt() -> list[Message]:
    assistant = Message(
        content=TextContent(
            type="text",
            text="""You are an experienced homebrewer with deep knowledge of the brewing process at homebrewer level, ingredients and styles.
            You are not focused on give a full recipe, just an overview of what styles are possible based on ingredients we already have in the inventory and by acquiring extra ingredients.
            Try to optimize the usage of the ingredients on inventory but  don't go out of the style, suggest acquiring new ingredients to stay inside the style guidelines.
            """,
        ),
        role="assistant",
    )
    role = "user"
    content = TextContent(
        type="text",
        text="""What are the styles I can brew with my Brewfather inventory?
        Don't be limit to the items in the inventory, but try to use as much as possible from the inventory.
        Use styles from the latest BJCP.
        """,
    )

    return [assistant, Message(content, role=role)]


@mcp.tool(
    name="list_inventory_categories",
    description="Lists the available inventory categories.",
)
async def inventory_categories() -> str:
    content = """
    Fermentables (Grains, Adjuncts, etc..)
    Hops
    Yeasts
    """

    return content

@mcp.tool(
    name="list_fermentables",
    description="List all the fermentables (malts, adjuncts, grains, etc) inventory.",
)
async def read_fermentables() -> str:
    try:
        params = ListQueryParams()
        params.limit = 50
        data = await brewfather_client.get_fermentables_list(params)

        formatted_response: list[str] = []
        for item in data.root:
            # Only include items with inventory > 0
            if item.inventory and float(item.inventory) > 0:
                formatted = f"""Name: {item.name}
Type: {item.type}
Supplier: {item.supplier}
Quantity: {item.inventory} kg
Identifier: {item.id}
"""

                formatted_response.append(formatted)

        return "---\n".join(formatted_response)
    except Exception:
        logger.exception("Error happened")
        raise


@mcp.tool(
    name="get_fermentable_detail",
    description="Detailed information of the fermentable item.",
)
async def read_fermentable_detail(identifier: str) -> str:
    logger.info("received request")

    try:
        item = await brewfather_client.get_fermentable_detail(identifier)

        formatted_response = f"""Name: {item.name}
Type: {item.type}
Supplier: {item.supplier}
Inventory: {item.inventory}
Origin: {item.origin}
Grain Category: {item.grain_category}
Potential: {item.potential}
Potential Percentage: {item.potential_percentage}
Color: {item.color}
Moisture: {item.moisture}
Protein: {item.protein}
Diastatic Power: {item.diastatic_power}
Friability: {item.friability}
Not Fermentable: {item.not_fermentable}
Max In Batch: {item.max_in_batch}
Coarse Fine Diff: {item.coarse_fine_diff}
Percent Extract Fine-Ground Dry Basis (FGDB): {item.fgdb}
Hidden: {item.hidden}
Notes: {item.notes}
User Notes: {item.user_notes}
Used In: {item.used_in}
Substitutes: {item.substitutes}
Cost Per Amount: {item.cost_per_amount}
Best Before Date: {item.best_before_date}
Manufacturing Date: {item.manufacturing_date}
Free Amino Nitrogen (FAN): {item.fan}
Percent Coarse-Ground Dry Basic (CGDB): {item.cgdb}
Acid: {item.acid}
ID: {item.id}
"""

        return formatted_response

    except Exception:
        logger.exception("Error happened")
        raise


@mcp.tool(
    name="list_hops",
    description="Lists all hops in inventory with their basic properties like alpha acids, quantity, and usage type.",
)
async def read_hops() -> str:
    logger.info("received request")

    try:
        params = ListQueryParams()
        params.limit = 50
        data = await brewfather_client.get_hops_list(params)

        formatted_response: list[str] = []
        for item in data.root:
            # Only include items with inventory > 0
            if item.inventory and float(item.inventory) > 0:
                formatted = f"""Identifier: {item.id}
Alpha Acids (A.A): {item.alpha}
Quantity: {item.inventory} grams
Name: {item.name}
Type: {item.type}
Use: {item.use}
"""

                formatted_response.append(formatted)

        return "---\n".join(formatted_response)
    except Exception:
        logger.exception("Error happened")
        raise


@mcp.tool(
    name="get_hop_detail",
    description="Detailed information about a specific hop including origin, characteristics, oil composition, and storage details.",
)
async def read_hops_detail(identifier: str) -> str:
    logger.info("received request")

    try:
        item = await brewfather_client.get_hop_detail(identifier)

        formatted = f"""Name: {item.name}
Type: {item.type}
Origin: {item.origin}
Use: {item.use}
Usage: {item.usage}
Alpha Acid (% A.A): {item.alpha}
Beta: {item.beta}
Inventory: {item.inventory}
Time: {item.time}
IBU: {item.ibu}
Oil: {item.oil}
Myrcene: {item.myrcene}
Caryophyllene: {item.caryophyllene}
Humulene: {item.humulene}
Cohumulone: {item.cohumulone}
Farnesene: {item.farnesene}
HSI: {item.hsi}
Year: {item.year}
Temp: {item.temp}
Amount: {item.amount}
Substitutes: {item.substitutes}
Used In: {item.used_in}
Notes: {item.notes}
User Notes: {item.user_notes}
Hidden: {item.hidden}
Best Before Date: {item.best_before_date}
Manufacturing Date: {item.manufacturing_date}
Version: {item.version}
ID: {item.id}
"""
        return formatted

    except:
        logger.exception("Error happened")
        raise


@mcp.tool(
    name="list_yeasts",
    description="Lists all yeasts in inventory with their basic properties like attenuation, quantity, and type.",
)
async def read_yeasts() -> str:
    logger.info("received request")

    try:
        params = ListQueryParams()
        params.limit = 50
        data = await brewfather_client.get_yeasts_list(params)

        formatted_response: list[str] = []
        for item in data.root:
            # Only include items with inventory > 0
            if item.inventory and float(item.inventory) > 0:
                formatted = f"""Identifier: {item.id}
Attenuation (%): {item.attenuation}
Quantity: {item.inventory} {item.unit}
Name: {item.name}
Type: {item.type}
"""

                formatted_response.append(formatted)

        return "---\n".join(formatted_response)
    except:
        logger.exception("Error happened")
        raise


@mcp.tool(
    name="get_yeast_detail",
    description="Detailed information about a specific yeast including manufacturer, specifications, temperature range, and storage details.",
)
async def read_yeasts_detail(identifier: str) -> str:
    logger.info("received request")

    try:
        item = await brewfather_client.get_yeast_detail(identifier)

        formatted = f"""Name: {item.name}
Type: {item.type}
Form: {item.form}
Laboratory: {item.laboratory}
Product ID: {item.product_id}
Inventory: {item.inventory}
Amount: {item.amount}
Unit: {item.unit}
Attenuation: {item.attenuation}
Min Attenuation: {item.min_attenuation}
Max Attenuation: {item.max_attenuation}
Flocculation: {item.flocculation}
Min Temp: {item.min_temp}
Max Temp: {item.max_temp}
Max ABV: {item.max_abv}
Cells Per Package: {item.cells_per_pkg}
Age Rate: {item.age_rate}
Ferments All: {item.ferments_all}
Description: {item.description}
User Notes: {item.user_notes}
Hidden: {item.hidden}
Best Before Date: {item.best_before_date}
Manufacturing Date: {item.manufacturing_date}
Timestamp: {item.timestamp.seconds if item.timestamp else 'N/A'}
Created: {item.created.seconds if item.created else 'N/A'}
Version: {item.version}
ID: {item.id}
Rev: {item.rev}
"""
        return formatted

    except Exception:
        logger.exception("Error happened")
        raise


@mcp.tool(
    name="inventory_summary",
    description="Creates a comprehensive overview of all inventory items including fermentables, hops, yeasts and miscellaneous items.",
)
async def inventory_summary() -> str:
    try:
        ctx = mcp.get_context()
        
        # Test each function individually with error handling
        try:
            fermentables = await get_fermentables_summary(brewfather_client)
            logger.info(f"Fermentables summary: {len(fermentables)} items")
        except Exception as e:
            logger.exception("Error getting fermentables summary")
            fermentables = []

        try:
            hops = await get_hops_summary(brewfather_client)
            logger.info(f"Hops summary: {len(hops)} items")
        except Exception as e:
            logger.exception("Error getting hops summary")
            hops = []

        try:
            yeasts = await get_yeast_summary(brewfather_client)
            logger.info(f"Yeasts summary: {len(yeasts)} items")
        except Exception as e:
            logger.exception("Error getting yeasts summary")
            yeasts = []

        try:
            miscs = await get_miscs_summary(brewfather_client)
            logger.info(f"Miscs summary: {len(miscs)} items")
        except Exception as e:
            logger.exception("Error getting miscs summary")
            miscs = []

        await ctx.info("API data gathered")

        response = "Fermentables:\n\n"
        for fermentable in fermentables:
            for k, v in fermentable.items():
                response += f"{k}: {v}\n"
            response += "\n"

        response += "\n---\n"

        response += "Hops:\n\n"
        for hop in hops:
            for k, v in hop.items():
                response += f"{k}: {v}\n"

        response += "\n---\n"

        response += "Yeasts:\n\n"
        for yeast in yeasts:
            for k, v in yeast.items():
                response += f"{k}: {v}\n"
            response += "\n"

        response += "\n---\n"

        response += "Miscellaneous Items:\n\n"
        for misc in miscs:
            for k, v in misc.items():
                response += f"{k}: {v}\n"
            response += "\n"

        await ctx.report_progress(100, 100)
        return response
    except Exception:
        logger.exception("Failed to show inventory summary")
        raise


# Batch Endpoints
@mcp.tool(
    name="list_batches",
    description="Lists all brew batches.",
)
async def read_batches_list() -> str:
    logger.info("received request for batches list")
    try:
        params = ListQueryParams()
        params.limit = 50
        data = await brewfather_client.get_batches_list(params)
        formatted_response: list[str] = []
        for item in data.root:
            brew_date_str = (
                datetime.fromtimestamp(item.brew_date / 1000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if item.brew_date
                else "N/A"
            )
            formatted = f"""ID: {item.id}
Name: {item.name}
Batch Number: {item.batch_no or 'N/A'}
Status: {item.status or 'N/A'}
Brewer: {item.brewer or 'N/A'}
Brew Date: {brew_date_str}
Recipe Name: {item.recipe_name}
"""
            formatted_response.append(formatted)
        return "---\n".join(formatted_response) if formatted_response else "No batches found."
    except Exception:
        logger.exception("Error happened while fetching batches list")
        raise


@mcp.tool(
    name="get_batch_detail",
    description="Get detailed information for a specific batch.",
)
async def read_batch_detail(batch_id: str) -> str:
    logger.info(f"received request for batch detail: {batch_id}")
    try:
        item = await brewfather_client.get_batch_detail(batch_id)
        brew_date_str = (
            datetime.fromtimestamp(item.brew_date / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if item.brew_date
            else "N/A"
        )
        # Format dates
        fermentation_start_str = (
            item.fermentation_start_date.strftime("%Y-%m-%d %H:%M:%S")
            if item.fermentation_start_date
            else "N/A"
        )
        fermentation_end_str = (
            item.fermentation_end_date.strftime("%Y-%m-%d %H:%M:%S")
            if item.fermentation_end_date
            else "N/A"
        )
        bottling_date_str = (
            item.bottling_date.strftime("%Y-%m-%d %H:%M:%S")
            if item.bottling_date
            else "N/A"
        )
        
        formatted_response = f"""Batch Details:
==============
ID: {item.id}
Name: {item.name}
Batch Number: {item.batch_no or 'N/A'}
Status: {item.status or 'N/A'}
Brewer: {item.brewer or 'N/A'}
Brewed: {'Yes' if item.brewed else 'No'}

Recipe Information:
------------------
Recipe Name: {getattr(item.recipe, 'name', 'N/A') if item.recipe else 'N/A'}
Recipe ID: {getattr(item.recipe, 'id', getattr(item, 'recipe_id', 'N/A'))}

Schedule:
---------
Brew Date: {brew_date_str}
Fermentation Start: {fermentation_start_str}
Fermentation End: {fermentation_end_str}
Bottling Date: {bottling_date_str}

Gravity & Alcohol:
-----------------
Original Gravity (OG): {item.measured_og or item.og or 'N/A'}
Final Gravity (FG): {item.measured_fg or item.fg or 'N/A'}
ABV: {item.measured_abv or item.abv or 'N/A'}%

Carbonation:
-----------
Type: {item.carbonation_type or 'N/A'}
Level: {item.carbonation_level or (item.recipe.carbonation if item.recipe else None) or 'N/A'} volumes

Tags: {', '.join(item.tags) if item.tags else 'None'}
"""
        
        # Add brew day measurements if any exist
        brew_measurements = []
        if item.measured_mash_ph:
            # Mash pH target is typically from water profile
            target_ph = getattr(item.recipe, 'mash', {}).get('ph') if item.recipe else None
            if target_ph:
                delta = item.measured_mash_ph - target_ph
                brew_measurements.append(f"Mash pH: {item.measured_mash_ph} ({delta:+.2f})")
            else:
                brew_measurements.append(f"Mash pH: {item.measured_mash_ph}")
        
        if item.measured_first_wort_gravity:
            brew_measurements.append(f"First Wort Gravity: {item.measured_first_wort_gravity}")
        
        if item.measured_pre_boil_gravity:
            # Compare to recipe pre-boil gravity
            target_pre_boil = getattr(item.recipe, 'pre_boil_gravity', None) if item.recipe else None
            if target_pre_boil:
                delta = item.measured_pre_boil_gravity - target_pre_boil
                brew_measurements.append(f"Pre-Boil Gravity: {item.measured_pre_boil_gravity} ({delta:+.3f})")
            else:
                brew_measurements.append(f"Pre-Boil Gravity: {item.measured_pre_boil_gravity}")
        
        if item.measured_boil_size:
            # Compare to recipe boil size
            target_boil_size = getattr(item.recipe, 'boil_size', None) if item.recipe else None
            if target_boil_size:
                delta = item.measured_boil_size - target_boil_size
                brew_measurements.append(f"Boil Size: {item.measured_boil_size}L ({delta:+.2f}L)")
            else:
                brew_measurements.append(f"Boil Size: {item.measured_boil_size}L")
        
        if item.measured_post_boil_gravity:
            # Compare to recipe post-boil gravity
            target_post_boil = getattr(item.recipe, 'post_boil_gravity', None) if item.recipe else None
            if target_post_boil:
                delta = item.measured_post_boil_gravity - target_post_boil
                brew_measurements.append(f"Post-Boil Gravity: {item.measured_post_boil_gravity} ({delta:+.3f})")
            else:
                brew_measurements.append(f"Post-Boil Gravity: {item.measured_post_boil_gravity}")
        
        if item.measured_kettle_size:
            brew_measurements.append(f"Kettle Size: {item.measured_kettle_size}L")
        
        if item.measured_og:
            # Compare to recipe OG
            target_og = getattr(item.recipe, 'og', None) if item.recipe else None
            if target_og:
                delta = item.measured_og - target_og
                brew_measurements.append(f"Measured OG: {item.measured_og} ({delta:+.3f})")
            else:
                brew_measurements.append(f"Measured OG: {item.measured_og}")
        
        if item.measured_batch_size:
            # Compare to recipe batch size
            target_batch_size = getattr(item.recipe, 'batch_size', None) if item.recipe else None
            if target_batch_size:
                delta = item.measured_batch_size - target_batch_size
                brew_measurements.append(f"Batch Size: {item.measured_batch_size}L ({delta:+.2f}L)")
            else:
                brew_measurements.append(f"Batch Size: {item.measured_batch_size}L")
        
        if item.measured_fermenter_top_up:
            brew_measurements.append(f"Fermenter Top-Up: {item.measured_fermenter_top_up}L")
        
        if brew_measurements:
            formatted_response += "\nBrew Day Measurements:\n---------------------\n"
            for measurement in brew_measurements:
                formatted_response += f"- {measurement}\n"
        
        # Add fermentation measurements if any exist
        fermentation_measurements = []
        if item.measured_fg:
            # Compare to recipe FG
            target_fg = getattr(item.recipe, 'fg', None) if item.recipe else None
            if target_fg:
                delta = item.measured_fg - target_fg
                fermentation_measurements.append(f"Measured FG: {item.measured_fg} ({delta:+.3f})")
            else:
                fermentation_measurements.append(f"Measured FG: {item.measured_fg}")
        
        if item.measured_abv:
            # Compare to recipe ABV
            target_abv = getattr(item.recipe, 'abv', None) if item.recipe else None
            if target_abv:
                delta = item.measured_abv - target_abv
                fermentation_measurements.append(f"Measured ABV: {item.measured_abv}% ({delta:+.2f}%)")
            else:
                fermentation_measurements.append(f"Measured ABV: {item.measured_abv}%")
        
        if item.measured_attenuation:
            # Compare to recipe attenuation
            target_attenuation = getattr(item.recipe, 'attenuation', None) if item.recipe else None
            if target_attenuation:
                delta = item.measured_attenuation - target_attenuation
                fermentation_measurements.append(f"Measured Attenuation: {item.measured_attenuation}% ({delta:+.2f}%)")
            else:
                fermentation_measurements.append(f"Measured Attenuation: {item.measured_attenuation}%")
        
        if item.measured_bottling_size:
            fermentation_measurements.append(f"Bottling Size: {item.measured_bottling_size}L")
        
        if item.measured_efficiency:
            # Compare to recipe brewhouse efficiency
            target_efficiency = getattr(item.recipe, 'efficiency', None) if item.recipe else None
            if target_efficiency:
                delta = item.measured_efficiency - target_efficiency
                fermentation_measurements.append(f"Overall Efficiency: {item.measured_efficiency}% ({delta:+.2f}%)")
            else:
                fermentation_measurements.append(f"Overall Efficiency: {item.measured_efficiency}%")
        
        if item.measured_mash_efficiency:
            # Compare to recipe mash efficiency
            target_mash_eff = getattr(item.recipe, 'mash_efficiency', None) if item.recipe else None
            if target_mash_eff:
                delta = item.measured_mash_efficiency - target_mash_eff
                fermentation_measurements.append(f"Mash Efficiency: {item.measured_mash_efficiency}% ({delta:+.2f}%)")
            else:
                fermentation_measurements.append(f"Mash Efficiency: {item.measured_mash_efficiency}%")
        
        if item.measured_kettle_efficiency:
            fermentation_measurements.append(f"Kettle Efficiency: {item.measured_kettle_efficiency}%")
        
        if item.measured_conversion_efficiency:
            fermentation_measurements.append(f"Conversion Efficiency: {item.measured_conversion_efficiency}%")
        
        if fermentation_measurements:
            formatted_response += "\nFermentation Measurements:\n-------------------------\n"
            for measurement in fermentation_measurements:
                formatted_response += f"- {measurement}\n"
        
        if item.notes:
            formatted_response += "\nNotes:\n"
            for note in item.notes:
                note_time = datetime.fromtimestamp(note.timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
                formatted_response += f"- [{note.type}] {note.note} ({note_time})\n"
        
        if item.measurements:
            formatted_response += "\nMeasurements:\n-------------\n"
            for measurement in item.measurements:
                meas_time = measurement.time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(measurement, 'time') and measurement.time else "N/A"
                comment = f" ({measurement.comment})" if hasattr(measurement, 'comment') and measurement.comment else ""
                formatted_response += f"- {measurement.type}: {measurement.value} {measurement.unit} [{meas_time}]{comment}\n"
        
        if item.measurement_devices:
            formatted_response += "\nMeasurement Devices:\n------------------\n"
            for device in item.measurement_devices:
                device_name = device.get('name', 'Unknown Device')
                device_type = device.get('type', 'N/A')
                formatted_response += f"- {device_name} ({device_type})\n"
        
        # Add recipe details if available
        if item.recipe:
            formatted_response += "\n\n" + "="*50 + "\n"
            formatted_response += "RECIPE DETAILS\n"
            formatted_response += "="*50 + "\n\n"
            formatted_response += format_recipe_details(item.recipe)
        
        # Add batch metadata
        formatted_response += "\n\nBatch Metadata:\n--------------\n"
        formatted_response += f"Batch ID: {item.id}\n"
        
        return formatted_response
    except Exception:
        logger.exception(f"Error happened while fetching batch detail for {batch_id}")
        raise


@mcp.tool(
    name="update_batch",
    description="Updates a batch's status or measured values.",
)
async def update_batch(
    batch_id: str,
    status: Optional[str] = None,
    measuredMashPh: Optional[float] = None,
    measuredBoilSize: Optional[float] = None,
    measuredFirstWortGravity: Optional[float] = None,
    measuredPreBoilGravity: Optional[float] = None,
    measuredPostBoilGravity: Optional[float] = None,
    measuredKettleSize: Optional[float] = None,
    measuredOg: Optional[float] = None,
    measuredFermenterTopUp: Optional[float] = None,
    measuredBatchSize: Optional[float] = None,
    measuredFg: Optional[float] = None,
    measuredBottlingSize: Optional[float] = None,
    carbonationTemp: Optional[float] = None,
) -> str:
    logger.info(f"received request to update batch: {batch_id}")
    update_data = {}
    if status:
        update_data["status"] = status
    if measuredMashPh is not None:
        update_data["measuredMashPh"] = measuredMashPh
    if measuredBoilSize is not None:
        update_data["measuredBoilSize"] = measuredBoilSize
    if measuredFirstWortGravity is not None:
        update_data["measuredFirstWortGravity"] = measuredFirstWortGravity
    if measuredPreBoilGravity is not None:
        update_data["measuredPreBoilGravity"] = measuredPreBoilGravity
    if measuredPostBoilGravity is not None:
        update_data["measuredPostBoilGravity"] = measuredPostBoilGravity
    if measuredKettleSize is not None:
        update_data["measuredKettleSize"] = measuredKettleSize
    if measuredOg is not None:
        update_data["measuredOg"] = measuredOg
    if measuredFermenterTopUp is not None:
        update_data["measuredFermenterTopUp"] = measuredFermenterTopUp
    if measuredBatchSize is not None:
        update_data["measuredBatchSize"] = measuredBatchSize
    if measuredFg is not None:
        update_data["measuredFg"] = measuredFg
    if measuredBottlingSize is not None:
        update_data["measuredBottlingSize"] = measuredBottlingSize
    if carbonationTemp is not None:
        update_data["carbonationTemp"] = carbonationTemp

    if not update_data:
        return "No update parameters provided."

    try:
        await brewfather_client.update_batch_detail(batch_id, update_data)
        return f"Batch {batch_id} updated successfully."
    except Exception:
        logger.exception(f"Error happened while updating batch {batch_id}")
        raise


# Recipe Endpoints
@mcp.tool(
    name="list_recipes",
    description="Lists all recipes.",
)
async def read_recipes_list() -> str:
    logger.info("received request for recipes list")
    try:
        params = ListQueryParams()
        params.limit = 100  # Increase limit to get more recipes
        data = await brewfather_client.get_recipes_list(params)
        formatted_response: list[str] = []
        for item in data.root:
            formatted = f"""ID: {item.id}
Name: {item.name}
Author: {item.author or 'N/A'}
Style: {item.style.name if item.style else 'N/A'}
Type: {item.type or 'N/A'}
"""
            formatted_response.append(formatted)
        return "---\n".join(formatted_response) if formatted_response else "No recipes found."
    except Exception:
        logger.exception("Error happened while fetching recipes list")
        raise


@mcp.tool(
    name="get_recipe_detail",
    description="Get detailed information for a specific recipe including ingredients, process details and specifications.",
)
async def read_recipe_detail(recipe_id: str) -> str:
    logger.info(f"received request for recipe detail: {recipe_id}")
    try:
        item = await brewfather_client.get_recipe_detail(recipe_id)
        return format_recipe_details(item)
    except Exception:
        logger.exception(f"Error happened while fetching recipe detail for {recipe_id}")
        raise


# Miscellaneous Inventory Endpoints
@mcp.tool(
    name="list_misc_items",
    description="Lists all miscellaneous inventory items.",
)
async def read_miscs_list() -> str:
    logger.info("received request for miscellaneous inventory list")
    try:
        params = ListQueryParams()
        params.limit = 50
        data = await brewfather_client.get_miscs_list(params)

        formatted_response: list[str] = []
        for item in data.root:
            # Only include items with inventory > 0
            if item.inventory and float(item.inventory) > 0:
                formatted = f"""ID: {item.id}
Name: {item.name}
Type: {item.type or 'N/A'}
Inventory: {item.inventory} units (actual unit depends on item)
Notes: {item.notes or 'N/A'}
"""
                formatted_response.append(formatted)
        return "---\n".join(formatted_response) if formatted_response else "No miscellaneous items found."
    except Exception:
        logger.exception("Error happened while fetching miscellaneous inventory list")
        raise


@mcp.tool(
    name="get_misc_detail",
    description="Get detailed information for a specific miscellaneous inventory item.",
)
async def read_misc_detail(item_id: str) -> str:
    logger.info(f"received request for miscellaneous item detail: {item_id}")
    try:
        # Assuming Miscellaneous model in types.py might be simple for list view.
        # For full details, a MiscellaneousDetail model would be needed.
        item = await brewfather_client.get_misc_detail(item_id)
        formatted_response = f"""ID: {item.id}
Name: {item.name}
Type: {item.type or 'N/A'}
Inventory: {item.inventory} units
Notes: {item.notes or 'N/A'}
"""
        # Add more fields if a more detailed model (e.g., MiscellaneousDetail) is implemented
        return formatted_response
    except Exception:
        logger.exception(f"Error happened while fetching miscellaneous item detail for {item_id}")
        raise


# Inventory Update Tools
@mcp.tool(
    name="update_fermentable_inventory",
    description="Sets the inventory amount for a specific fermentable.",
)
async def update_fermentable_inventory_tool(item_id: str, inventory_amount: float) -> str:
    logger.info(f"Tool: update_fermentable_inventory_tool called for item {item_id} with amount {inventory_amount}")
    try:
        await brewfather_client.update_fermentable_inventory(item_id, inventory_amount)
        return f"Fermentable inventory for item {item_id} updated to {inventory_amount} kg."
    except Exception:
        logger.exception(f"Error updating fermentable inventory for item {item_id}")
        raise


@mcp.tool(
    name="update_hop_inventory",
    description="Sets the inventory amount for a specific hop.",
)
async def update_hop_inventory_tool(item_id: str, inventory_amount: float) -> str:
    logger.info(f"Tool: update_hop_inventory_tool called for item {item_id} with amount {inventory_amount}")
    try:
        await brewfather_client.update_hop_inventory(item_id, inventory_amount)
        return f"Hop inventory for item {item_id} updated to {inventory_amount} grams."
    except Exception:
        logger.exception(f"Error updating hop inventory for item {item_id}")
        raise


@mcp.tool(
    name="update_misc_inventory",
    description="Sets the inventory amount for a specific miscellaneous item.",
)
async def update_misc_inventory_tool(item_id: str, inventory_amount: float) -> str:
    logger.info(f"Tool: update_misc_inventory_tool called for item {item_id} with amount {inventory_amount}")
    try:
        await brewfather_client.update_misc_inventory(item_id, inventory_amount)
        return f"Miscellaneous inventory for item {item_id} updated to {inventory_amount} units."
    except Exception:
        logger.exception(f"Error updating miscellaneous inventory for item {item_id}")
        raise


@mcp.tool(
    name="update_yeast_inventory",
    description="Sets the inventory amount for a specific yeast.",
)
async def update_yeast_inventory_tool(item_id: str, inventory_amount: float) -> str:
    logger.info(f"Tool: update_yeast_inventory_tool called for item {item_id} with amount {inventory_amount}")
    try:
        await brewfather_client.update_yeast_inventory(item_id, inventory_amount)
        return f"Yeast inventory for item {item_id} updated to {inventory_amount} packets."
    except Exception:
        logger.exception(f"Error updating yeast inventory for item {item_id}")
        raise


# Brewtracker endpoints - Enhanced brewing information
@mcp.tool(
    name="get_batch_brewtracker",
    description="Get detailed brewing process guidance and timeline for a batch",
)
async def get_batch_brewtracker(batch_id: str) -> str:
    """Get brewtracker status with step-by-step brewing guidance"""
    try:
        tracker = await brewfather_client.get_batch_brewtracker(batch_id)
        
        # Handle case where no brewtracker data exists
        if not tracker.name or not tracker.stages:
            return f"No brewtracker data available for batch {batch_id}. This batch may not have brewing process tracking enabled."
        
        formatted_response = f"""BREWING PROCESS TRACKER: {tracker.name}
{'='*60}

Status: {'ACTIVE' if tracker.active else 'INACTIVE'} | Stage {tracker.stage + 1} of {len(tracker.stages)}
Completed: {'Yes' if tracker.completed else 'No'} | Notifications: {'On' if tracker.notify else 'Off'}

"""
        
        for i, stage in enumerate(tracker.stages):
            status_icon = "🔄" if i == tracker.stage and tracker.active else "✅" if i < tracker.stage else "⏳"
            formatted_response += f"{status_icon} STAGE {i + 1}: {stage.name.upper()}\n"
            formatted_response += f"Duration: {stage.duration // 60} min | Current Step: {stage.step + 1}/{len(stage.steps)}\n"
            formatted_response += f"Position: {stage.position // 60} min {'(PAUSED)' if stage.paused else ''}\n\n"
            
            for j, step in enumerate(stage.steps):
                step_icon = "▶️" if i == tracker.stage and j == stage.step and tracker.active else "✅" if j < stage.step or i < tracker.stage else "⏸️"
                step_name = step.name if step.name else f"{step.type.title()} Step"
                formatted_response += f"  {step_icon} {step_name}"
                
                if step.time > 0:
                    formatted_response += f" @ {step.time // 60} min"
                if step.value:
                    formatted_response += f" ({step.value}°C)"
                formatted_response += "\n"
                
                if step.description:
                    formatted_response += f"     📝 {step.description}\n"
                
                if step.tooltip and step.tooltip != step.description:
                    formatted_response += f"     💡 {step.tooltip}\n"
                    
                formatted_response += "\n"
            
            formatted_response += "\n"
        
        return formatted_response

    except Exception:
        logger.exception("Error getting brewtracker data")
        raise


@mcp.tool(
    name="get_batch_last_reading",
    description="Get the most recent sensor reading from brewing devices for a batch",
)
async def get_batch_last_reading(batch_id: str) -> str:
    """Get last sensor reading with current brewing status"""
    try:
        reading = await brewfather_client.get_batch_last_reading(batch_id)
        
        from datetime import datetime
        reading_time = datetime.fromtimestamp(reading.time / 1000).strftime("%Y-%m-%d %H:%M:%S")
        
        formatted_response = f"""LATEST SENSOR READING
{'='*40}

Device: {reading.name} ({reading.device_type})
Reading Time: {reading_time}
Device ID: {reading.id}

MEASUREMENTS:
-------------"""
        
        if reading.temp is not None:
            formatted_response += f"\n🌡️  Temperature: {reading.temp}°C"
        
        if reading.sg is not None:
            formatted_response += f"\n🍺  Specific Gravity: {reading.sg:.4f}"
            
        if reading.battery is not None:
            battery_icon = "🔋" if reading.battery > 50 else "🪫" if reading.battery > 20 else "🚨"
            formatted_response += f"\n{battery_icon}  Battery: {reading.battery:.1f}%"
            
        if reading.rssi is not None:
            signal_icon = "📶" if reading.rssi > -50 else "📊" if reading.rssi > -70 else "📱"
            formatted_response += f"\n{signal_icon}  Signal: {reading.rssi:.1f} dBm"
            
        if reading.target_temp is not None:
            formatted_response += f"\n🎯  Target Temp: {reading.target_temp}°C"
            
        if reading.ph is not None:
            formatted_response += f"\n🧪  pH: {reading.ph}"
            
        if reading.pressure is not None:
            formatted_response += f"\n⚡  Pressure: {reading.pressure}"
        
        return formatted_response

    except Exception:
        logger.exception("Error getting last reading data")
        raise


@mcp.tool(
    name="get_batch_readings_summary",
    description="Get a summary of recent sensor readings for a batch (limited to avoid large responses)",
)
async def get_batch_readings_summary(batch_id: str, limit: int = 10) -> str:
    """Get summary of recent readings with trends"""
    try:
        readings = await brewfather_client.get_batch_readings(batch_id)
        
        if not readings.root:
            return "No sensor readings found for this batch."
        
        # Get the most recent readings (limited to avoid huge responses)
        recent_readings = readings.root[-limit:] if len(readings.root) > limit else readings.root
        
        from datetime import datetime
        
        formatted_response = f"""RECENT SENSOR READINGS SUMMARY
{'='*50}

Total readings available: {len(readings.root)}
Showing latest {len(recent_readings)} readings:

"""
        
        for reading in recent_readings:
            reading_time = datetime.fromtimestamp(reading.time / 1000).strftime("%m-%d %H:%M")
            
            device_name = reading.name or reading.id or reading.type or "Unknown Device"
            line = f"{reading_time} | {device_name}"
            
            if reading.temp is not None:
                line += f" | {reading.temp:.1f}°C"
            if reading.sg is not None:
                line += f" | SG {reading.sg:.4f}"
            if reading.battery is not None:
                line += f" | {reading.battery:.0f}%"
                
            formatted_response += line + "\n"
        
        # Add trend analysis if we have enough data
        if len(recent_readings) >= 3:
            formatted_response += "\nTREND ANALYSIS:\n"
            first = recent_readings[0]
            last = recent_readings[-1]
            
            if first.temp is not None and last.temp is not None:
                temp_change = last.temp - first.temp
                temp_trend = "↗️ Rising" if temp_change > 0.5 else "↘️ Falling" if temp_change < -0.5 else "➡️ Stable"
                formatted_response += f"Temperature: {temp_trend} ({temp_change:+.1f}°C)\n"
                
            if first.sg is not None and last.sg is not None:
                sg_change = last.sg - first.sg
                sg_trend = "↗️ Rising" if sg_change > 0.002 else "↘️ Falling" if sg_change < -0.002 else "➡️ Stable"
                formatted_response += f"Specific Gravity: {sg_trend} ({sg_change:+.4f})\n"
        
        return formatted_response

    except Exception:
        logger.exception("Error getting readings summary")
        raise


# Recipe Creation Tools
@mcp.tool(
    name="get_recipe_enums",
    description="Returns valid enum values for recipe creation from defined type system.",
)
async def get_recipe_enums() -> str:
    """Get valid enum values for recipe creation from defined type system"""

    # Format all enum values from our type system
    recipe_types = "\n".join(f"- {rt.value}" for rt in RecipeType)
    hop_uses = "\n".join(f"- {hu.value}" for hu in HopUse)
    hop_forms = "\n".join(f"- {hf.value}" for hf in HopForm)
    hop_usages = "\n".join(f"- {hu.value}" for hu in HopUsage)
    yeast_forms = "\n".join(f"- {yf.value}" for yf in YeastForm)
    yeast_types = "\n".join(f"- {yt.value}" for yt in YeastType)
    flocculation_types = "\n".join(f"- {ft.value}" for ft in Flocculation)
    misc_uses = "\n".join(f"- {mu.value}" for mu in MiscUse)
    misc_types = "\n".join(f"- {mt.value}" for mt in MiscType)
    fermentable_types = "\n".join(f"- {ft.value}" for ft in FermentableType)
    fermentable_grain_groups = "\n".join(f"- {fgg.value}" for fgg in FermentableGrainGroup)
    mash_step_types = "\n".join(f"- {mst.value}" for mst in MashStepType)
    fermentation_step_types = "\n".join(f"- {fst.value}" for fst in FermentationStepType)

    enums_info = f"""RECIPE ENUM VALUES
=====================================

These are the valid enum values you can use when creating recipes.

Recipe Types:
{recipe_types}

Hop Uses:
{hop_uses}

Hop Forms:
{hop_forms}

Hop Usage (purpose):
{hop_usages}

Yeast Forms:
{yeast_forms}

Yeast Types:
{yeast_types}

Flocculation Types:
{flocculation_types}

Misc Uses:
{misc_uses}

Misc Types:
{misc_types}

Fermentable Types:
{fermentable_types}

Fermentable Grain Groups:
{fermentable_grain_groups}

Mash Step Types:
{mash_step_types}

Fermentation Step Types:
{fermentation_step_types}
"""
    return enums_info


@mcp.tool(
    name="create_recipe",
    description="Creates a complete recipe with ingredients and process steps, returning valid Brewfather JSON for import.",
)
async def create_recipe(
    name: str,
    author: Optional[str] = "MCP Generated",
    recipe_type: Optional[str] = RecipeType.ALL_GRAIN.value,
    style_name: Optional[str] = "Custom Recipe",
    batch_size: Optional[float] = 21.0,
    boil_time: Optional[int] = 60,
    fermentables: Optional[list] = None,
    hops: Optional[list] = None,
    yeasts: Optional[list] = None,
    miscs: Optional[list] = None,
    mash_steps: Optional[list] = None,
    fermentation_temp: Optional[float] = None,
) -> str:
    """
    Creates a recipe with ingredients and process steps.

    Args:
        name: Recipe name (required)
        author: Recipe author (default: "MCP Generated")
        recipe_type: "All Grain", "Extract", or "Partial Mash" (default: "All Grain")
        style_name: Beer style name (default: "Custom Recipe")
        batch_size: Target batch volume in liters (default: 21.0)
        boil_time: Boil duration in minutes (default: 60)
        fermentables: List of fermentable dicts with keys: name, amount (kg), color (optional)
        hops: List of hop dicts with keys: name, amount (g), alpha (%), use, time (min)
        yeasts: List of yeast dicts with keys: name, amount, form (YeastForm values)
        miscs: List of misc dicts with keys: name, amount, use, time (optional)
        mash_steps: List of mash step dicts with keys: stepTemp (°C), stepTime (min), name (optional)
        fermentation_temp: Primary fermentation temperature in °C (optional)

    Returns:
        JSON string formatted for Brewfather import
    """
    logger.info(f"Creating recipe: {name}")

    try:
        # Import here to avoid circular imports
        from brewfather_mcp.types.recipe import RecipeDetail, RecipeStyle
        from brewfather_mcp.types.fermentable import RecipeFermentable
        from brewfather_mcp.types.hop import RecipeHop
        from brewfather_mcp.types.yeast import RecipeYeast
        from brewfather_mcp.types.misc import RecipeMisc
        from brewfather_mcp.types.base import MashSchedule, MashStep, FermentationSchedule, FermentationStep
        import brewfather_mcp.utils as utils
        import json

        # Validate required fields
        if not name or not name.strip():
            raise ValueError("Recipe name is required")

        # Validate recipe type
        valid_types = [rt.value for rt in RecipeType]
        if recipe_type not in valid_types:
            raise ValueError(f"Invalid recipe type '{recipe_type}'. Valid types: {', '.join(valid_types)}")

        # Set defaults for empty lists
        fermentables = fermentables or []
        hops = hops or []
        yeasts = yeasts or []
        miscs = miscs or []
        mash_steps = mash_steps or []

        # Generate unique recipe ID (simple approach for now)
        import uuid
        recipe_id = str(uuid.uuid4()).replace('-', '')[:22].upper()

        # Create recipe object
        recipe = RecipeDetail(
            id=recipe_id,
            name=name.strip(),
            author=author.strip() if author else "MCP Generated",
            type=recipe_type,
            batch_size=batch_size,
            boil_time=boil_time,
            style=RecipeStyle(name=style_name or "Custom Recipe"),
            fermentables=[],
            hops=[],
            yeasts=[],
            miscs=[],
            mash=None if not mash_steps else MashSchedule(
                name="Custom Mash Schedule",
                steps=[
                    MashStep(
                        name=step.get("name", ""),
                        stepTemp=step["stepTemp"],
                        stepTime=step["stepTime"],
                        type="Temperature"
                    ) for step in mash_steps
                ]
            ),
            fermentation=FermentationSchedule(
                name="Custom Fermentation Schedule",
                steps=[
                    FermentationStep(
                        stepTemp=fermentation_temp or 20,
                        stepTime=14,  # Default 14 days primary
                        type="Primary"
                    )
                ] if fermentation_temp else []
            ) if fermentation_temp else None
        )

        # Add fermentables
        for ferm_data in fermentables:
            if not ferm_data.get("name") or not ferm_data.get("amount"):
                logger.warning(f"Skipping fermentable with missing name or amount: {ferm_data}")
                continue

            fermentable = RecipeFermentable(
                name=ferm_data["name"],
                type="Grain",  # Default type for fermentables
                amount=float(ferm_data["amount"]),
                color=float(ferm_data.get("color", 3.0)) if ferm_data.get("color") else None,
                id=None  # Let Brewfather assign ID
            )
            recipe.fermentables.append(fermentable)

        # Add hops
        for hop_data in hops:
            if not all(k in hop_data for k in ["name", "amount", "alpha", "use", "time"]):
                logger.warning(f"Skipping hop with missing required fields: {hop_data}")
                continue

            hop = RecipeHop(
                name=hop_data["name"],
                type=HopForm.PELLET,  # Default type for hops
                amount=float(hop_data["amount"]),
                alpha=float(hop_data["alpha"]),
                use=hop_data["use"],
                time=int(hop_data["time"]),
                id=None  # Let Brewfather assign ID
            )
            recipe.hops.append(hop)

        # Add yeasts
        for yeast_data in yeasts:
            if not all(k in yeast_data for k in ["name", "amount", "form"]):
                logger.warning(f"Skipping yeast with missing required fields: {yeast_data}")
                continue

            yeast = RecipeYeast(
                name=yeast_data["name"],
                type=YeastType.ALE,  # Default type for yeast
                amount=float(yeast_data["amount"]),
                form=yeast_data["form"],
                id=None  # Let Brewfather assign ID
            )
            recipe.yeasts.append(yeast)

        # Add miscellaneous ingredients
        for misc_data in miscs:
            if not all(k in misc_data for k in ["name", "amount", "use"]):
                logger.warning(f"Skipping misc with missing required fields: {misc_data}")
                continue

            misc = RecipeMisc(
                name=misc_data["name"],
                amount=float(misc_data["amount"]),
                use=misc_data["use"],
                time=int(misc_data["time"]) if misc_data.get("time") else None,
                id=None  # Let Brewfather assign ID
            )
            recipe.miscs.append(misc)

        # Convert to JSON
        recipe_dict = recipe.model_dump(by_alias=True, exclude_none=True)

        # Clean up the JSON for import - remove calculated fields
        cleanup_fields = [
            'og', 'fg', 'ibu', 'color', 'abv', 'attenuation',
            'buGuRatio', 'rbRatio', 'styleConformity',
            'fermentableIbu', 'extraGravity', 'diastaticPower',
            'sumDryHopPerLiter', 'avgWeightedHopstandTemp',
            'yeastToleranceExceededBy', 'manualFg',
            'hopStandMinutes', 'carbonationStyle'
        ]

        for field in cleanup_fields:
            recipe_dict.pop(field, None)

        json_output = json.dumps(recipe_dict, indent=2, ensure_ascii=False)

        logger.info(f"Successfully created recipe '{name}' with {len(recipe.fermentables)} fermentables, {len(recipe.hops)} hops, {len(recipe.yeasts)} yeasts")

        return f"""RECIPE JSON FOR BREWFATHER IMPORT
====================================

Recipe Name: {name}
Type: {recipe_type}
Batch Size: {batch_size}L
Boil Time: {boil_time} minutes

Ingredients:
- Fermentables: {len(recipe.fermentables)}
- Hops: {len(recipe.hops)}
- Yeasts: {len(recipe.yeasts)}
- Misc: {len(recipe.miscs)}

IMPORT INSTRUCTIONS:
1. Copy the JSON below
2. In Brewfather, go to Recipes → Import → Brewfather JSON
3. Paste the JSON and import

JSON:
-----
{json_output}

Note: Equipment profiles and calculated values (OG, FG, IBU, ABV) will be
set by Brewfather after import. This recipe contains the essential brewing
information needed to make the beer.
"""

    except Exception as e:
        logger.exception(f"Error creating recipe '{name}'")
        raise ValueError(f"Failed to create recipe: {str(e)}")
