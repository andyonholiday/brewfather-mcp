import json
import pytest
import httpx
from pathlib import Path
from respx import MockRouter
from typing import List, Tuple

from brewfather_mcp.api import BrewfatherClient, BASE_URL, ListQueryParams
from brewfather_mcp.types import (
    Batch,
    BatchDetail,
    BatchList,
    FermentableDetail,
    FermentableList,
    HopDetail,
    HopList,
    Misc,
    MiscList,
    Recipe,
    RecipeDetail,
    RecipeList,
    YeastDetail,
    YeastList,
)


@pytest.fixture
def client(monkeypatch) -> BrewfatherClient:
    """Create a BrewfatherClient instance with mock credentials."""
    monkeypatch.setenv("BREWFATHER_API_USER_ID", "testuser")
    monkeypatch.setenv("BREWFATHER_API_KEY", "testkey")
    return BrewfatherClient()


def load_debug_json(filename: str) -> dict | list:
    """Load JSON data from debug directory."""
    debug_path = Path(__file__).parent.parent / "debug" / filename
    with open(debug_path, "r") as f:
        return json.load(f)


def get_debug_files_by_type(pattern: str) -> List[Tuple[str, str]]:
    """Get all debug JSON files matching a regex pattern.
    
    Args:
        pattern: Regex pattern to match against filenames (without .json extension).
                 Use a capture group to extract the test_id part.
    
    Returns:
        List of tuples: (filename, test_id)
    """
    import re
    debug_dir = Path(__file__).parent.parent / "debug"
    files = []
    
    for json_file in debug_dir.glob("*.json"):
        # Skip files with query parameters in the name
        if "?" in json_file.name:
            continue
            
        filename = json_file.name
        stem = json_file.stem  # filename without .json
        
        match = re.match(pattern, stem)
        if match:
            # Extract test_id from first capture group, or use "list" as fallback
            test_id = match.group(1) if match.groups() and match.group(1) else "list"
            files.append((filename, test_id))
    
    return files


version_mock = {
    "_rev": "foo",
    "_version": "2.8.1",
    "_timestamp": {"_seconds": 1644033488, "_nanoseconds": 107000000},
    "_timestamp_ms": 1644033488107,
    "_created": {"_seconds": 1621674499, "_nanoseconds": 901000000},
}


@pytest.mark.asyncio
async def test_http_error_handling_get(
    client: BrewfatherClient, respx_mock: MockRouter
):
    respx_mock.get(f"{BASE_URL}/inventory/fermentables").mock(
        return_value=httpx.Response(500)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await client.get_fermentables_list()


@pytest.mark.asyncio
async def test_http_error_handling_patch(
    client: BrewfatherClient, respx_mock: MockRouter
):
    batch_id = "error_batch"
    respx_mock.patch(f"{BASE_URL}/batches/{batch_id}").mock(
        return_value=httpx.Response(401)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await client.update_batch_detail(batch_id, {"status": "Failed"})


class TestFermentables:
    @pytest.mark.asyncio
    async def test_get_fermentables_list(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        mock_data = [
            {
                "_id": "f1",
                "name": "Pilsner Malt",
                "inventory": 10.0,
                "type": "Grain",
                "supplier": "Weyermann",
            }
        ]
        respx_mock.get(f"{BASE_URL}/inventory/fermentables").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_fermentables_list()
        assert isinstance(result, FermentableList)
        assert len(result.root) == 1
        assert result.root[0].id == "f1"
        assert result.root[0].name == "Pilsner Malt"

    @pytest.mark.asyncio
    async def test_get_fermentable_detail(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        item_id = "f1_detail"
        mock_data = {
            "_id": item_id,
            "name": "CaraPils",
            "inventory": 5.0,
            "potential": 1.035,
            "type": "Grain",
            "supplier": "Briess",
            "color": 2.0,
            "potentialPercentage": 80.0,
            "potential": 1.035,
        } | version_mock
        respx_mock.get(f"{BASE_URL}/inventory/fermentables/{item_id}").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_fermentable_detail(item_id)
        assert isinstance(result, FermentableDetail)
        assert result.id == item_id
        assert result.potential == 1.035

    @pytest.mark.asyncio
    async def test_update_fermentable_inventory(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        item_id = "f_inv_update"
        inventory_amount = 25.5
        respx_mock.patch(f"{BASE_URL}/inventory/fermentables/{item_id}").mock(
            return_value=httpx.Response(200)
        )
        await client.update_fermentable_inventory(item_id, inventory_amount)
        assert len(respx_mock.calls) == 1
        request = respx_mock.calls.last.request
        assert request.method == "PATCH"
        assert json.loads(request.content) == {"inventory": inventory_amount}

    @pytest.mark.parametrize("filename,test_id", get_debug_files_by_type(r"^inventory_fermentables(?:_(.+))?$"))
    @pytest.mark.asyncio
    async def test_fermentables_data_validation(self, client: BrewfatherClient, respx_mock: MockRouter, filename: str, test_id: str):
        """Test that all fermentables debug data validates correctly."""
        mock_data = load_debug_json(filename)
        
        if filename == "inventory_fermentables.json":
            # Test list endpoint
            respx_mock.get(f"{BASE_URL}/inventory/fermentables").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_fermentables_list()
            assert isinstance(result, FermentableList)
            assert len(result.root) == len(mock_data)
        else:
            # Test detail endpoint - extract ID from filename
            item_id = filename.replace("inventory_fermentables_", "").replace(".json", "")
            respx_mock.get(f"{BASE_URL}/inventory/fermentables/{item_id}").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_fermentable_detail(item_id)
            assert isinstance(result, FermentableDetail)
            assert result.id == item_id


class TestHops:
    @pytest.mark.asyncio
    async def test_get_hops_list(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        mock_data = [
            {
                "_id": "h1",
                "name": "Cascade",
                "inventory": 200.0,
                "alpha": 5.5,
                "type": "Pellet",
            }
        ]
        respx_mock.get(f"{BASE_URL}/inventory/hops").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_hops_list()
        assert isinstance(result, HopList)
        assert len(result.root) == 1
        assert result.root[0].name == "Cascade"

    @pytest.mark.asyncio
    async def test_get_hop_detail(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        item_id = "h1_detail"
        mock_data = {
            "_id": item_id,
            "name": "Citra",
            "inventory": 100.0,
            "alpha": 12.0,
            "type": "Pellet",
            "use": "Aroma",
        } | version_mock
        respx_mock.get(f"{BASE_URL}/inventory/hops/{item_id}").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_hop_detail(item_id)
        assert isinstance(result, HopDetail)
        assert result.alpha == 12.0

    @pytest.mark.asyncio
    async def test_update_hop_inventory(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        item_id = "h_inv_update"
        inventory_amount = 150.0
        respx_mock.patch(f"{BASE_URL}/inventory/hops/{item_id}").mock(
            return_value=httpx.Response(200)
        )
        await client.update_hop_inventory(item_id, inventory_amount)
        assert len(respx_mock.calls) == 1
        request = respx_mock.calls.last.request
        assert json.loads(request.content) == {"inventory": inventory_amount}

    @pytest.mark.parametrize("filename,test_id", get_debug_files_by_type(r"^inventory_hops(?:_(.+))?$"))
    @pytest.mark.asyncio
    async def test_hops_data_validation(self, client: BrewfatherClient, respx_mock: MockRouter, filename: str, test_id: str):
        """Test that all hops debug data validates correctly."""
        mock_data = load_debug_json(filename)
        
        if filename == "inventory_hops.json":
            # Test list endpoint
            respx_mock.get(f"{BASE_URL}/inventory/hops").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_hops_list()
            assert isinstance(result, HopList)
            assert len(result.root) == len(mock_data)
        else:
            # Test detail endpoint - extract ID from filename
            item_id = filename.replace("inventory_hops_", "").replace(".json", "")
            respx_mock.get(f"{BASE_URL}/inventory/hops/{item_id}").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_hop_detail(item_id)
            assert isinstance(result, HopDetail)
            assert result.id == item_id


class TestYeasts:
    @pytest.mark.asyncio
    async def test_get_yeasts_list(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        mock_data = [
            {
                "_id": "y1",
                "name": "US-05",
                "inventory": 5.0,
                "attenuation": 81,
                "type": "Ale",
            }
        ]
        respx_mock.get(f"{BASE_URL}/inventory/yeasts").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_yeasts_list()
        assert isinstance(result, YeastList)
        assert len(result.root) == 1
        assert result.root[0].attenuation == 81

    @pytest.mark.asyncio
    async def test_get_yeast_detail(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        item_id = "y1_detail"
        mock_data = {
            "_id": item_id,
            "name": "WLP001",
            "inventory": 2.0,
            "attenuation": 78,
            "laboratory": "White Labs",
            "type": "Ale",
        } | version_mock
        respx_mock.get(f"{BASE_URL}/inventory/yeasts/{item_id}").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_yeast_detail(item_id)
        assert isinstance(result, YeastDetail)
        assert result.laboratory == "White Labs"

    @pytest.mark.asyncio
    async def test_update_yeast_inventory(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        item_id = "y_inv_update"
        inventory_amount = 10.0
        respx_mock.patch(f"{BASE_URL}/inventory/yeasts/{item_id}").mock(
            return_value=httpx.Response(200)
        )
        await client.update_yeast_inventory(item_id, inventory_amount)
        assert len(respx_mock.calls) == 1
        request = respx_mock.calls.last.request
        assert json.loads(request.content) == {"inventory": inventory_amount}

    @pytest.mark.parametrize("filename,test_id", get_debug_files_by_type(r"^inventory_yeasts(?:_(.+))?$"))
    @pytest.mark.asyncio
    async def test_yeasts_data_validation(self, client: BrewfatherClient, respx_mock: MockRouter, filename: str, test_id: str):
        """Test that all yeasts debug data validates correctly."""
        mock_data = load_debug_json(filename)
        
        if filename == "inventory_yeasts.json":
            # Test list endpoint
            respx_mock.get(f"{BASE_URL}/inventory/yeasts").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_yeasts_list()
            assert isinstance(result, YeastList)
            assert len(result.root) == len(mock_data)
        else:
            # Test detail endpoint - extract ID from filename
            item_id = filename.replace("inventory_yeasts_", "").replace(".json", "")
            respx_mock.get(f"{BASE_URL}/inventory/yeasts/{item_id}").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_yeast_detail(item_id)
            assert isinstance(result, YeastDetail)
            assert result.id == item_id


class TestBatches:
    @pytest.mark.asyncio
    async def test_get_batches_list_success(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        mock_response_data = [
            {
                "_id": "batch1",
                "name": "Test Batch",
                "batchNo": 1,
                "recipe": {"name": "Test Recipe", "_id": "recipe1"},
            }
        ]
        respx_mock.get(f"{BASE_URL}/batches").mock(
            return_value=httpx.Response(200, json=mock_response_data)
        )
        result = await client.get_batches_list()
        assert isinstance(result, BatchList)
        assert len(result.root) == 1
        assert result.root[0].id == "batch1"
        assert result.root[0].name == "Test Batch"

    @pytest.mark.asyncio
    async def test_get_batches_list_empty(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        respx_mock.get(f"{BASE_URL}/batches").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await client.get_batches_list()
        assert isinstance(result, BatchList)
        assert len(result.root) == 0

    @pytest.mark.asyncio
    async def test_get_batch_detail_success(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        batch_id = "b_detail"
        mock_data = {
            "_id": batch_id,
            "name": "Detailed Batch",
            "status": "Fermenting",
            "recipe": {"name": "Detailed Recipe", "_id": "recipe2"},
            "batchNo": 2,
        } | version_mock
        respx_mock.get(f"{BASE_URL}/batches/{batch_id}").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_batch_detail(batch_id)
        assert isinstance(result, Batch)
        assert result.id == batch_id
        assert result.status == "Fermenting"

    @pytest.mark.asyncio
    async def test_update_batch_detail_success(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        batch_id = "b_update"
        payload = {"status": "Completed", "measuredFg": 1.010}
        respx_mock.patch(f"{BASE_URL}/batches/{batch_id}").mock(
            return_value=httpx.Response(200)
        )
        await client.update_batch_detail(batch_id, payload)
        assert len(respx_mock.calls) == 1
        request = respx_mock.calls.last.request
        assert request.method == "PATCH"
        assert str(request.url) == f"{BASE_URL}/batches/{batch_id}"
        assert json.loads(request.content) == payload

    @pytest.mark.parametrize("filename,test_id", get_debug_files_by_type(r"^batches(?:_([A-Za-z0-9]+))?$"))
    @pytest.mark.asyncio
    async def test_batches_data_validation(self, client: BrewfatherClient, respx_mock: MockRouter, filename: str, test_id: str):
        """Test that all batches debug data validates correctly."""
        mock_data = load_debug_json(filename)
        
        if filename == "batches.json":
            # Test list endpoint
            respx_mock.get(f"{BASE_URL}/batches").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_batches_list()
            assert isinstance(result, BatchList)
            assert len(result.root) == len(mock_data)
        else:
            # Test detail endpoint - extract ID from filename
            batch_id = filename.replace("batches_", "").replace(".json", "")
            respx_mock.get(f"{BASE_URL}/batches/{batch_id}").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_batch_detail(batch_id)
            assert isinstance(result, BatchDetail)
            assert result.id == batch_id


class TestRecipes:
    @pytest.mark.asyncio
    async def test_get_recipes_list_success(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        mock_data = [{"_id": "r1", "name": "My IPA", "type": "All Grain"}]
        respx_mock.get(f"{BASE_URL}/recipes").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_recipes_list()
        assert isinstance(result, RecipeList)
        assert len(result.root) == 1
        assert result.root[0].name == "My IPA"

    @pytest.mark.asyncio
    async def test_get_recipe_detail_success(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        recipe_id = "r_detail"
        mock_data = {
            "_id": recipe_id,
            "name": "Detailed Recipe",
            "author": "Brewer Joe",
        }
        respx_mock.get(f"{BASE_URL}/recipes/{recipe_id}").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_recipe_detail(recipe_id)
        assert isinstance(result, Recipe)
        assert result.id == recipe_id
        assert result.author == "Brewer Joe"

    @pytest.mark.parametrize("filename,test_id", get_debug_files_by_type(r"^recipes(?:_(.+))?$"))
    @pytest.mark.asyncio
    async def test_recipes_data_validation(self, client: BrewfatherClient, respx_mock: MockRouter, filename: str, test_id: str):
        """Test that all recipes debug data validates correctly."""
        mock_data = load_debug_json(filename)
        
        if filename == "recipes.json":
            # Test list endpoint
            respx_mock.get(f"{BASE_URL}/recipes").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_recipes_list()
            assert isinstance(result, RecipeList)
            assert len(result.root) == len(mock_data)
        else:
            # Test detail endpoint - extract ID from filename
            recipe_id = filename.replace("recipes_", "").replace(".json", "")
            respx_mock.get(f"{BASE_URL}/recipes/{recipe_id}").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_recipe_detail(recipe_id)
            assert isinstance(result, RecipeDetail)
            assert result.id == recipe_id


class TestMiscellaneous:
    @pytest.mark.asyncio
    async def test_get_miscs_list_success(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        mock_data = [
            {"_id": "m1", "name": "Irish Moss", "inventory": 50.0, "type": "Fining"}
        ]
        respx_mock.get(f"{BASE_URL}/inventory/miscs").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_miscs_list()
        assert isinstance(result, MiscList)
        assert len(result.root) == 1
        assert result.root[0].type == "Fining"

    @pytest.mark.asyncio
    async def test_get_misc_detail_success(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        item_id = "m_detail"
        mock_data = {
            "_id": item_id,
            "name": "Whirlfloc",
            "notes": "Use 1 tablet per 5 gallons",
        } | version_mock
        respx_mock.get(f"{BASE_URL}/inventory/miscs/{item_id}").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_misc_detail(item_id)
        assert isinstance(result, Misc)
        assert result.id == item_id
        assert result.notes == "Use 1 tablet per 5 gallons"

    @pytest.mark.asyncio
    async def test_update_misc_inventory(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        item_id = "m_inv_update"
        inventory_amount = 20.0
        respx_mock.patch(f"{BASE_URL}/inventory/miscs/{item_id}").mock(
            return_value=httpx.Response(200)
        )
        await client.update_misc_inventory(item_id, inventory_amount)
        assert len(respx_mock.calls) == 1
        request = respx_mock.calls.last.request
        assert json.loads(request.content) == {"inventory": inventory_amount}

    @pytest.mark.parametrize("filename,test_id", get_debug_files_by_type(r"^inventory_miscs(?:_(.+))?$"))
    @pytest.mark.asyncio
    async def test_miscs_data_validation(self, client: BrewfatherClient, respx_mock: MockRouter, filename: str, test_id: str):
        """Test that all misc debug data validates correctly."""
        mock_data = load_debug_json(filename)

        if filename == "inventory_miscs.json":
            # Test list endpoint
            respx_mock.get(f"{BASE_URL}/inventory/miscs").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_miscs_list()
            assert isinstance(result, MiscList)
            assert len(result.root) == len(mock_data)
        else:
            # Test detail endpoint - extract ID from filename
            item_id = filename.replace("inventory_miscs_", "").replace(".json", "")
            respx_mock.get(f"{BASE_URL}/inventory/miscs/{item_id}").mock(
                return_value=httpx.Response(200, json=mock_data)
            )
            result = await client.get_misc_detail(item_id)
            assert isinstance(result, Misc)
            assert result.id == item_id


class TestPagination:
    """Tests for the cursor-based pagination in _get_paginated_list."""

    @pytest.mark.asyncio
    async def test_single_page_fewer_than_limit(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        """When API returns fewer items than limit, no second page is fetched."""
        mock_data = [
            {"_id": f"f{i}", "name": f"Malt {i}", "inventory": 1.0, "type": "Grain"}
            for i in range(3)
        ]
        respx_mock.get(f"{BASE_URL}/inventory/fermentables").mock(
            return_value=httpx.Response(200, json=mock_data)
        )
        result = await client.get_fermentables_list()
        assert isinstance(result, FermentableList)
        assert len(result.root) == 3
        # Only one request should have been made
        assert len(respx_mock.calls) == 1

    @pytest.mark.asyncio
    async def test_multi_page_pagination(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        """When first page is full (count == limit), a second page is fetched."""
        # The default limit in _get_paginated_list is 50
        page_size = 50

        page1_data = [
            {"_id": f"f{i:03d}", "name": f"Malt {i}", "inventory": 1.0, "type": "Grain"}
            for i in range(page_size)
        ]
        page2_data = [
            {"_id": f"f{i:03d}", "name": f"Malt {i}", "inventory": 1.0, "type": "Grain"}
            for i in range(page_size, page_size + 10)
        ]

        call_count = 0

        def side_effect(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(200, json=page1_data)
            else:
                return httpx.Response(200, json=page2_data)

        respx_mock.get(f"{BASE_URL}/inventory/fermentables").mock(side_effect=side_effect)

        result = await client.get_fermentables_list()
        assert isinstance(result, FermentableList)
        assert len(result.root) == page_size + 10
        assert call_count == 2

        # Verify the second request used start_after
        second_request = respx_mock.calls[1].request
        assert "start_after" in str(second_request.url)
        assert f"f{page_size - 1:03d}" in str(second_request.url)

    @pytest.mark.asyncio
    async def test_three_page_pagination(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        """Verify pagination works across three pages."""
        page_size = 50

        pages = [
            [
                {"_id": f"f{p * page_size + i:03d}", "name": f"Malt {p * page_size + i}", "inventory": 1.0, "type": "Grain"}
                for i in range(page_size)
            ]
            for p in range(2)
        ]
        # Third page with fewer items (last page)
        pages.append([
            {"_id": f"f{2 * page_size + i:03d}", "name": f"Malt {2 * page_size + i}", "inventory": 1.0, "type": "Grain"}
            for i in range(5)
        ])

        call_count = 0

        def side_effect(request):
            nonlocal call_count
            page_idx = call_count
            call_count += 1
            return httpx.Response(200, json=pages[page_idx])

        respx_mock.get(f"{BASE_URL}/inventory/fermentables").mock(side_effect=side_effect)

        result = await client.get_fermentables_list()
        assert len(result.root) == 2 * page_size + 5
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_pagination_respects_max_pages(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        """When max_pages is reached, pagination stops even if more data exists."""
        page_size = 50

        # Always return a full page (simulating unlimited data)
        def side_effect(request):
            return httpx.Response(200, json=[
                {"_id": f"f{i}", "name": f"Malt {i}", "inventory": 1.0, "type": "Grain"}
                for i in range(page_size)
            ])

        respx_mock.get(f"{BASE_URL}/inventory/fermentables").mock(side_effect=side_effect)

        result = await client.get_fermentables_list()
        # max_pages is 10, so we get 10 pages * 50 items = 500 items
        # (but items will have duplicate IDs since mock returns same data - that's OK for this test)
        assert len(result.root) == page_size * client.max_pages
        assert len(respx_mock.calls) == client.max_pages

    @pytest.mark.asyncio
    async def test_pagination_empty_first_page(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        """When first page is empty, no further pages are fetched."""
        respx_mock.get(f"{BASE_URL}/inventory/fermentables").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await client.get_fermentables_list()
        assert len(result.root) == 0
        assert len(respx_mock.calls) == 1

    @pytest.mark.asyncio
    async def test_pagination_exact_page_boundary(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        """When results exactly fill one page, a second empty page is fetched."""
        page_size = 50
        full_page = [
            {"_id": f"f{i:03d}", "name": f"Malt {i}", "inventory": 1.0, "type": "Grain"}
            for i in range(page_size)
        ]

        call_count = 0

        def side_effect(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(200, json=full_page)
            else:
                return httpx.Response(200, json=[])

        respx_mock.get(f"{BASE_URL}/inventory/fermentables").mock(side_effect=side_effect)

        result = await client.get_fermentables_list()
        assert len(result.root) == page_size
        # Two calls: first returns full page, second returns empty
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_pagination_with_custom_params(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        """Pagination preserves custom query params like inventory_exists."""
        mock_data = [
            {"_id": "f1", "name": "Malt", "inventory": 5.0, "type": "Grain"}
        ]
        respx_mock.get(f"{BASE_URL}/inventory/fermentables").mock(
            return_value=httpx.Response(200, json=mock_data)
        )

        params = ListQueryParams()
        params.inventory_exists = True
        result = await client.get_fermentables_list(params)

        assert len(result.root) == 1
        first_request = respx_mock.calls[0].request
        assert "inventory_exists=true" in str(first_request.url)

    @pytest.mark.asyncio
    async def test_pagination_start_after_carries_filters(
        self, client: BrewfatherClient, respx_mock: MockRouter
    ):
        """On subsequent pages, query filters (inventory_exists etc.) are preserved."""
        page_size = 50

        page1_data = [
            {"_id": f"h{i:03d}", "name": f"Hop {i}", "inventory": 10.0, "alpha": 5.0, "type": "Pellet"}
            for i in range(page_size)
        ]
        page2_data = [
            {"_id": f"h{page_size + i:03d}", "name": f"Hop {page_size + i}", "inventory": 10.0, "alpha": 5.0, "type": "Pellet"}
            for i in range(3)
        ]

        call_count = 0

        def side_effect(request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(200, json=page1_data)
            else:
                return httpx.Response(200, json=page2_data)

        respx_mock.get(f"{BASE_URL}/inventory/hops").mock(side_effect=side_effect)

        params = ListQueryParams()
        params.inventory_exists = True
        result = await client.get_hops_list(params)

        assert len(result.root) == page_size + 3
        # Verify second request still has inventory_exists filter
        second_request = respx_mock.calls[1].request
        assert "inventory_exists=true" in str(second_request.url)
        assert "start_after" in str(second_request.url)
