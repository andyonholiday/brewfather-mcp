# type: ignore

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from brewfather_mcp.server import (
    inventory_categories,
    read_fermentables,
    read_fermentable_detail,
    read_hops,
    read_hops_detail,
    read_yeasts,
    read_yeasts_detail,
    inventory_summary,
    styles_based_inventory_prompt,
    read_batches_list,
    read_batch_detail,
    update_batch,
    read_recipes_list,
    read_recipe_detail,
    read_miscs_list,
    read_misc_detail,
    update_fermentable_inventory_tool,
    update_hop_inventory_tool,
    update_misc_inventory_tool,
    update_yeast_inventory_tool,
)
from brewfather_mcp.api import BrewfatherClient
from brewfather_mcp.types import (
    Batch,
    BatchList,
    FermentableList,
    HopList,
    Misc,
    MiscList,
    Recipe,
    RecipeList,
    YeastList,
)
from datetime import datetime


@pytest.fixture
def mock_brewfather_client(mocker):
    mocker.patch("os.getenv", "credential")
    client = AsyncMock(spec=BrewfatherClient)

    fermentable = MagicMock(
        name="Test Malt",
        type="Grain",
        supplier="Test Supplier",
        inventory=5.0,
        origin="Test Country",
        grain_category="Base",
        potential=1.037,
        potential_percentage=80.0,
        color=3.5,
        moisture=4.0,
        protein=11.0,
        diastatic_power=70,
        friability=80,
        not_fermentable=False,
        max_in_batch=100,
        coarse_fine_diff=1.0,
        fgdb=80,
        hidden=False,
        notes="Test notes",
        user_notes="",
        used_in="",
        substitutes="",
        cost_per_amount=None,
        best_before_date=None,
        manufacturing_date=None,
        fan=None,
        cgdb=None,
        acid=None,
        id="test-id",
    )

    hop = MagicMock(
        name="Test Hop",
        type="Pellet",
        origin="US",
        use="Boil",
        usage="Both",
        alpha=5.5,
        beta=None,
        inventory=100,
        time=60,
        ibu=0,
        oil=None,
        myrcene=None,
        caryophyllene=None,
        humulene=None,
        cohumulone=None,
        farnesene=None,
        hsi=None,
        year=None,
        temp=None,
        amount=None,
        substitutes="",
        used_in="",
        notes="",
        user_notes="",
        hidden=False,
        best_before_date=None,
        manufacturing_date=None,
        version="2.11.6",
        id="test-hop-id",
    )

    yeast = MagicMock(
        name="Test Yeast",
        type="Ale",
        form="Dry",
        laboratory="Test Lab",
        product_id="TY-01",
        inventory=2,
        amount=1,
        unit="pkg",
        attenuation=75,
        min_attenuation=None,
        max_attenuation=None,
        flocculation="Medium",
        min_temp=18,
        max_temp=24,
        max_abv=None,
        cells_per_pkg=None,
        age_rate=None,
        ferments_all=False,
        description="Test yeast description",
        user_notes="",
        hidden=False,
        best_before_date=None,
        manufacturing_date=None,
        timestamp=MagicMock(seconds=1613000000),
        created=MagicMock(seconds=1612000000),
        version="2.10.5",
        id="test-yeast-id",
        rev="abc123",
    )

    fermentables_list = MagicMock(spec=FermentableList)
    fermentables_list.root = [fermentable]
    client.get_fermentables_list.return_value = fermentables_list
    client.get_fermentable_detail.return_value = fermentable

    hops_list = MagicMock(spec=HopList)
    hops_list.root = [hop]
    client.get_hops_list.return_value = hops_list
    client.get_hop_detail.return_value = hop

    yeasts_list = MagicMock(spec=YeastList)
    yeasts_list.root = [yeast]
    client.get_yeasts_list.return_value = yeasts_list
    client.get_yeast_detail.return_value = yeast

    # Mock Batch data - remove spec to avoid attribute restrictions
    mock_recipe = MagicMock()
    mock_recipe.name = "Test Recipe"
    
    batch = MagicMock()
    batch.id = "test-batch-id"
    batch.name = "Test Batch"
    batch.batch_no = 1
    batch.status = "Fermenting"
    batch.brewer = "Test Brewer"
    batch.brew_date = int(datetime.now().timestamp() * 1000) # milliseconds
    batch.recipe = mock_recipe
    batch.recipe_id = "test-recipe-id"
    batch.brewed = True
    batch.fermentation_start_date = None
    batch.fermentation_end_date = None
    batch.bottling_date = None
    batch.og = None
    batch.fg = None
    batch.abv = None
    batch.carbonation_type = None
    batch.carbonation_level = None
    batch.notes = []
    batch.tags = []
    batch.measurements = []
    batch.measurement_devices = []
    # Add measured values that might be used in calculations
    batch.measured_og = None
    batch.measured_fg = None
    batch.measured_abv = None
    batch.measured_mash_ph = None
    batch.measured_first_wort_gravity = None
    batch.measured_pre_boil_gravity = None
    batch.measured_post_boil_gravity = None
    batch.measured_batch_size = None
    batch.measured_boil_size = None
    batch.measured_kettle_size = None
    batch.measured_fermenter_top_up = None
    batch.measured_bottling_size = None
    batch.measured_attenuation = None
    batch.measured_efficiency = None
    batch.measured_mash_efficiency = None
    batch.measured_kettle_efficiency = None
    batch.measured_conversion_efficiency = None
    batches_list = MagicMock(spec=BatchList)
    batches_list.root = [batch]
    client.get_batches_list.return_value = batches_list
    client.get_batch_detail.return_value = batch
    client.update_batch_detail.return_value = None # Typically PATCH doesn't return content

    # Mock Recipe data - remove spec to avoid attribute restrictions
    mock_style = MagicMock()
    mock_style.name = "Test Style"
    mock_style.category = "1"
    mock_style.type = "A"
    mock_style.style_guide = "BJCP 2021"
    
    mock_created = MagicMock()
    mock_created.to_datetime.return_value.strftime.return_value = "2023-01-01 10:00:00"
    
    mock_timestamp = MagicMock()
    mock_timestamp.to_datetime.return_value.strftime.return_value = "2023-01-01 11:00:00"
    
    recipe = MagicMock()
    recipe.id = "test-recipe-id"
    recipe.name = "Test Recipe"
    recipe.author = "Test Author"
    recipe.style = mock_style
    recipe.type = "All Grain"
    recipe.created = mock_created
    recipe.timestamp = mock_timestamp
    recipe.public = False
    recipe.tags = ["IPA", "hoppy"]
    recipe.style_conformity = True
    recipe.batch_size = 20.0
    recipe.boil_size = 25.0
    recipe.boil_time = 60
    recipe.efficiency = 75.0
    recipe.mash_efficiency = 80.0
    recipe.og = 1.050
    recipe.og_plato = 12.4
    recipe.fg = 1.010
    recipe.ibu = 40
    recipe.ibu_formula = "Tinseth"
    recipe.color = 6.0
    recipe.abv = 5.2
    recipe.attenuation = 80.0
    recipe.bu_gu_ratio = 0.8
    recipe.carbonation = 2.4
    recipe.pre_boil_gravity = 1.040
    recipe.fermentables = []
    recipe.hops = []
    recipe.yeasts = []
    recipe.miscs = []
    recipe.notes = "Test recipe notes"
    recipe.hidden = False
    recipes_list = MagicMock(spec=RecipeList)
    recipes_list.root = [recipe]
    client.get_recipes_list.return_value = recipes_list
    client.get_recipe_detail.return_value = recipe

    # Mock Miscellaneous data - remove spec to avoid attribute restrictions
    misc_item = MagicMock()
    misc_item.id = "test-misc-id"
    misc_item.name = "Test Misc Item"
    misc_item.type = "Fining"
    misc_item.inventory = 10.0
    misc_item.notes = "Test notes for misc"
    miscs_list = MagicMock(spec=MiscList)
    miscs_list.root = [misc_item]
    client.get_miscs_list.return_value = miscs_list
    client.get_misc_detail.return_value = misc_item

    # Mock inventory update methods
    client.update_fermentable_inventory.return_value = None
    client.update_hop_inventory.return_value = None
    client.update_misc_inventory.return_value = None
    client.update_yeast_inventory.return_value = None

    return client


@pytest.fixture
def mock_mcp_context():
    context = AsyncMock()
    context.info = AsyncMock()
    context.report_progress = AsyncMock()
    return context


class TestBrewfatherMCP:
    @pytest.mark.asyncio
    async def test_inventory_categories(self):
        result = await inventory_categories()
        assert "Fermentables" in result
        assert "Hops" in result
        assert "Yeasts" in result

    @pytest.mark.asyncio
    async def test_read_fermentables(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_fermentables()
            assert "Test Malt" in result
            assert "Grain" in result
            assert "5.0 kg" in result

    @pytest.mark.asyncio
    async def test_read_fermentable_detail(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_fermentable_detail("test-id")
            assert "Test Malt" in result
            assert "Test Supplier" in result
            assert "Test Country" in result

    @pytest.mark.asyncio
    async def test_read_hops(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_hops()
            assert "Test Hop" in result
            assert "5.5" in result
            assert "100 grams" in result

    @pytest.mark.asyncio
    async def test_read_hops_detail(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_hops_detail("test-hop-id")
            assert "Test Hop" in result
            assert "Pellet" in result
            assert "US" in result

    @pytest.mark.asyncio
    async def test_read_yeasts(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_yeasts()
            assert "Test Yeast" in result
            assert "75" in result
            assert "Quantity: 2" in result

    @pytest.mark.asyncio
    async def test_read_yeasts_detail(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_yeasts_detail("test-yeast-id")
            assert "Test Yeast" in result
            assert "Test Lab" in result
            assert "Medium" in result

    @pytest.mark.asyncio
    async def test_inventory_summary(self, mock_brewfather_client, mock_mcp_context):
        with (
            patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client),
            patch(
                "brewfather_mcp.server.mcp.get_context", return_value=mock_mcp_context
            ),
            patch(
                "brewfather_mcp.inventory.get_fermentables_summary",
                return_value=[{"Name": "Test Malt", "Inventory": "5.0 kg"}],
            ),
            patch(
                "brewfather_mcp.inventory.get_hops_summary",
                return_value=[{"Name": "Test Hop", "Inventory": "100 g"}],
            ),
            patch(
                "brewfather_mcp.inventory.get_yeast_summary",
                return_value=[{"Name": "Test Yeast", "Inventory": "2 pkg"}],
            ),
        ):
            result = await inventory_summary()
            assert "Fermentables:" in result
            assert "Hops:" in result
            assert "Yeasts:" in result
            assert "Test Malt" in result
            assert "Test Hop" in result
            assert "Test Yeast" in result
            mock_mcp_context.report_progress.assert_called_with(100, 100)

    @pytest.mark.asyncio
    async def test_styles_based_inventory_prompt(self):
        messages = await styles_based_inventory_prompt()
        assert len(messages) == 2
        assert messages[0].role == "assistant"
        assert messages[1].role == "user"
        assert "BJCP" in messages[1].content.text

    @pytest.mark.asyncio
    async def test_error_handling_read_fermentables(self, mock_brewfather_client):
        mock_brewfather_client.get_fermentables_list.side_effect = Exception(
            "API error"
        )
        with (
            patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client),
            patch("brewfather_mcp.server.logger") as mock_logger,
        ):
            with pytest.raises(Exception):
                await read_fermentables()

            mock_logger.exception.assert_called_once()

    # --- Batch Endpoint Tests ---
    @pytest.mark.asyncio
    async def test_read_batches_list_success(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_batches_list()
            mock_brewfather_client.get_batches_list.assert_called_once()
            assert "Name: Test Batch" in result
            assert "Batch Number: 1" in result
            assert "Status: Fermenting" in result

    @pytest.mark.asyncio
    async def test_read_batches_list_error(self, mock_brewfather_client):
        mock_brewfather_client.get_batches_list.side_effect = Exception("API Error Batches")
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client), \
             patch("brewfather_mcp.server.logger") as mock_logger:
            with pytest.raises(Exception, match="API Error Batches"):
                await read_batches_list()
            mock_logger.exception.assert_called_once_with("Error happened while fetching batches list")

    @pytest.mark.asyncio
    async def test_read_batch_detail_success(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_batch_detail("test-batch-id")
            mock_brewfather_client.get_batch_detail.assert_called_once_with("test-batch-id")
            assert "Name: Test Batch" in result
            assert "Recipe Name: Test Recipe" in result

    @pytest.mark.asyncio
    async def test_read_batch_detail_error(self, mock_brewfather_client):
        mock_brewfather_client.get_batch_detail.side_effect = Exception("API Error Batch Detail")
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client), \
             patch("brewfather_mcp.server.logger") as mock_logger:
            with pytest.raises(Exception, match="API Error Batch Detail"):
                await read_batch_detail("test-batch-id")
            mock_logger.exception.assert_called_once_with("Error happened while fetching batch detail for test-batch-id")

    @pytest.mark.asyncio
    async def test_update_batch_success(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            update_payload = {"status": "Completed"}
            result = await update_batch(batch_id="test-batch-id", status="Completed")
            mock_brewfather_client.update_batch_detail.assert_called_once_with("test-batch-id", update_payload)
            assert result == "Batch test-batch-id updated successfully."

    @pytest.mark.asyncio
    async def test_update_batch_no_params(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await update_batch(batch_id="test-batch-id")
            mock_brewfather_client.update_batch_detail.assert_not_called()
            assert result == "No update parameters provided."

    @pytest.mark.asyncio
    async def test_update_batch_error(self, mock_brewfather_client):
        mock_brewfather_client.update_batch_detail.side_effect = Exception("API Error Update Batch")
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client), \
             patch("brewfather_mcp.server.logger") as mock_logger:
            with pytest.raises(Exception, match="API Error Update Batch"):
                await update_batch(batch_id="test-batch-id", status="Failed")
            mock_logger.exception.assert_called_once_with("Error happened while updating batch test-batch-id")

    # --- Recipe Endpoint Tests ---
    @pytest.mark.asyncio
    async def test_read_recipes_list_success(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_recipes_list()
            mock_brewfather_client.get_recipes_list.assert_called_once()
            assert "Name: Test Recipe" in result
            assert "Author: Test Author" in result

    @pytest.mark.asyncio
    async def test_read_recipes_list_error(self, mock_brewfather_client):
        mock_brewfather_client.get_recipes_list.side_effect = Exception("API Error Recipes")
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client), \
             patch("brewfather_mcp.server.logger") as mock_logger:
            with pytest.raises(Exception, match="API Error Recipes"):
                await read_recipes_list()
            mock_logger.exception.assert_called_once_with("Error happened while fetching recipes list")

    @pytest.mark.asyncio
    async def test_read_recipe_detail_success(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_recipe_detail("test-recipe-id")
            mock_brewfather_client.get_recipe_detail.assert_called_once_with("test-recipe-id")
            assert "Recipe: Test Recipe" in result
            assert "Name: Test Style" in result

    @pytest.mark.asyncio
    async def test_read_recipe_detail_error(self, mock_brewfather_client):
        mock_brewfather_client.get_recipe_detail.side_effect = Exception("API Error Recipe Detail")
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client), \
             patch("brewfather_mcp.server.logger") as mock_logger:
            with pytest.raises(Exception, match="API Error Recipe Detail"):
                await read_recipe_detail("test-recipe-id")
            mock_logger.exception.assert_called_once_with("Error happened while fetching recipe detail for test-recipe-id")

    # --- Miscellaneous Inventory Endpoint Tests ---
    @pytest.mark.asyncio
    async def test_read_miscs_list_success(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_miscs_list()
            mock_brewfather_client.get_miscs_list.assert_called_once()
            assert "Name: Test Misc Item" in result
            assert "Type: Fining" in result

    @pytest.mark.asyncio
    async def test_read_miscs_list_error(self, mock_brewfather_client):
        mock_brewfather_client.get_miscs_list.side_effect = Exception("API Error Miscs")
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client), \
             patch("brewfather_mcp.server.logger") as mock_logger:
            with pytest.raises(Exception, match="API Error Miscs"):
                await read_miscs_list()
            mock_logger.exception.assert_called_once_with("Error happened while fetching miscellaneous inventory list")

    @pytest.mark.asyncio
    async def test_read_misc_detail_success(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            result = await read_misc_detail("test-misc-id")
            mock_brewfather_client.get_misc_detail.assert_called_once_with("test-misc-id")
            assert "Name: Test Misc Item" in result
            assert "Notes: Test notes for misc" in result

    @pytest.mark.asyncio
    async def test_read_misc_detail_error(self, mock_brewfather_client):
        mock_brewfather_client.get_misc_detail.side_effect = Exception("API Error Misc Detail")
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client), \
             patch("brewfather_mcp.server.logger") as mock_logger:
            with pytest.raises(Exception, match="API Error Misc Detail"):
                await read_misc_detail("test-misc-id")
            mock_logger.exception.assert_called_once_with("Error happened while fetching miscellaneous item detail for test-misc-id")

    # --- Inventory Update Tool Tests ---
    @pytest.mark.asyncio
    async def test_update_fermentable_inventory_tool_success(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            item_id = "f123"
            amount = 10.5
            result = await update_fermentable_inventory_tool(item_id, amount)
            mock_brewfather_client.update_fermentable_inventory.assert_called_once_with(item_id, amount)
            assert result == f"Fermentable inventory for item {item_id} updated to {amount} kg."

    @pytest.mark.asyncio
    async def test_update_fermentable_inventory_tool_error(self, mock_brewfather_client):
        mock_brewfather_client.update_fermentable_inventory.side_effect = Exception("API Error Update Fermentable")
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client), \
             patch("brewfather_mcp.server.logger") as mock_logger:
            with pytest.raises(Exception, match="API Error Update Fermentable"):
                await update_fermentable_inventory_tool("f123", 10.0)
            mock_logger.exception.assert_called_once_with("Error updating fermentable inventory for item f123")

    @pytest.mark.asyncio
    async def test_update_hop_inventory_tool_success(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            item_id = "h123"
            amount = 200.0
            result = await update_hop_inventory_tool(item_id, amount)
            mock_brewfather_client.update_hop_inventory.assert_called_once_with(item_id, amount)
            assert result == f"Hop inventory for item {item_id} updated to {amount} grams."

    @pytest.mark.asyncio
    async def test_update_misc_inventory_tool_success(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            item_id = "m123"
            amount = 5.0
            result = await update_misc_inventory_tool(item_id, amount)
            mock_brewfather_client.update_misc_inventory.assert_called_once_with(item_id, amount)
            assert result == f"Miscellaneous inventory for item {item_id} updated to {amount} units."

    @pytest.mark.asyncio
    async def test_update_yeast_inventory_tool_success(self, mock_brewfather_client):
        with patch("brewfather_mcp.server.brewfather_client", mock_brewfather_client):
            item_id = "y123"
            amount = 3.0
            result = await update_yeast_inventory_tool(item_id, amount)
            mock_brewfather_client.update_yeast_inventory.assert_called_once_with(item_id, amount)
            assert result == f"Yeast inventory for item {item_id} updated to {amount} packets."
