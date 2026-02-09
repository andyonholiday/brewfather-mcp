from enum import StrEnum
import logging
import os
import httpx
import urllib.parse

logger = logging.getLogger(__name__)
from .types import (
    FermentableDetail,
    FermentableList,
    HopDetail,
    HopList,
    InventoryCategory,
    MiscDetail,
    MiscList,
    RecipeDetail,
    RecipeList,
    YeastDetail,
    YeastList,
    BatchDetail,
    BatchList,
)
from .types.brewtracker import BrewTrackerStatus, BatchReadingsList, LastReading

BASE_URL: str = "https://api.brewfather.app/v2"

class OrderByDirection(StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"

class ListQueryParams:
    inventory_negative: bool | None = None
    complete: bool | None = None
    inventory_exists: bool | None = None
    limit: int | None = None
    start_after: str | None = None
    order_by: str | None = None
    order_by_direction: OrderByDirection | None = None

    def as_query_param_str(self) -> str | None:
        params = []

        if self.inventory_negative is not None:
            params.append(f"inventory_negative={'true' if self.inventory_negative else 'false'}")

        if self.complete is not None:
            params.append(f"complete={'true' if self.complete else 'false'}")

        if self.inventory_exists is not None:
            params.append(f"inventory_exists={'true' if self.inventory_exists else 'false'}")

        if self.limit:
            params.append(f"limit={self.limit}")

        if self.start_after:
            params.append(f"start_after={urllib.parse.quote_plus(self.start_after)}")

        if self.order_by:
            params.append(f"order_by={urllib.parse.quote_plus(self.order_by)}")

        if self.order_by_direction:
            params.append(f"order_by_direction={self.order_by_direction}")

        if params:
            return "&".join(params)
        else:
            return None

class BrewfatherClient:
    """Client for interacting with the Brewfather API."""

    def __init__(self):
        user_id = os.getenv("BREWFATHER_API_USER_ID")
        api_key = os.getenv("BREWFATHER_API_KEY")

        if not user_id or not api_key:
            raise ValueError(
                "Missing Brewfather credentials in the environment variables: BREWFATHER_API_USER_ID or BREWFATHER_API_KEY"
            )

        self.auth = httpx.BasicAuth(user_id, api_key)
        self.max_pages = 10  # Safety limit to prevent infinite loops

    async def _make_request(self, url: str) -> str:
        async with httpx.AsyncClient(auth=self.auth) as client:
            response = await client.get(url)
            response.raise_for_status()
            # Write response to a file for debugging when debug mode is enabled
            if os.getenv("BREWFATHER_MCP_DEBUG"):
                debug_dir = os.path.join(os.path.dirname(__file__), "..", "..", "debug")
                os.makedirs(debug_dir, exist_ok=True)
                debug_filename = url[len(BASE_URL) + 1:].split('?')[0].replace("/", "_").replace(":", "_") + ".json"
                debug_path = os.path.join(debug_dir, debug_filename)
                with open(debug_path, "w") as debug_file:
                    debug_file.write(response.text)
            return response.text

    async def _make_patch_request(self, url: str, data: dict) -> None:
        async with httpx.AsyncClient(auth=self.auth) as client:
            response = await client.patch(url, json=data)
            response.raise_for_status()

    async def _make_post_request(self, url: str, data: dict) -> str:
        async with httpx.AsyncClient(auth=self.auth) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.text

    def _build_url(
        self,
        endpoint: str,
        id: str | None = None,
        query_params: ListQueryParams | None = None,
    ) -> str:
        """Build a URL for the Brewfather API.

        Args:
            endpoint: The API endpoint (e.g., 'recipes', 'batches', 'inventory/fermentables')
            id: Optional ID for detail endpoints
            query_params: Optional query parameters
        """
        url = f"{BASE_URL}/{endpoint}"
        if id:
            url = f"{url}/{id}"
        if query_params:
            url += f"?{query_params.as_query_param_str()}"
        return url

    async def _get_paginated_list(
        self,
        endpoint: str,
        model_class,
        query_params: ListQueryParams | None = None,
    ):
        """Fetch all pages of a list endpoint using cursor pagination.

        Args:
            endpoint: The API endpoint to query
            model_class: The Pydantic model class to validate responses
            query_params: Query parameters including filters and limit

        Returns:
            A model instance with all results from all pages
        """
        all_items = []
        current_params = query_params or ListQueryParams()

        # Set a reasonable limit per page if not specified
        if not current_params.limit:
            current_params.limit = 50

        page_count = 0
        while page_count < self.max_pages:
            url = self._build_url(endpoint, query_params=current_params)
            json_response = await self._make_request(url)
            page_result = model_class.model_validate_json(json_response)

            # Add items from this page
            all_items.extend(page_result.root)

            # Check if there are more pages
            # If we got fewer items than the limit, we've reached the end
            if len(page_result.root) < current_params.limit:
                break

            # Set start_after to the ID of the last item for next page
            if page_result.root:
                current_params.start_after = page_result.root[-1].id
            else:
                break

            page_count += 1

        if page_count >= self.max_pages:
            logger.warning(
                f"Reached max page limit ({self.max_pages}) for endpoint '{endpoint}'. "
                f"Total items fetched: {len(all_items)}. There may be more items available."
            )

        logger.info(f"Fetched {len(all_items)} total items from '{endpoint}' across {page_count + 1} page(s)")

        # Return a new model instance with all collected items
        return model_class(root=all_items)

    # Inventory endpoints
    async def get_fermentables_list(
        self, query_params: ListQueryParams | None = None
    ) -> FermentableList:
        return await self._get_paginated_list(
            f"inventory/{InventoryCategory.FERMENTABLES}",
            FermentableList,
            query_params
        )

    async def get_fermentable_detail(self, id: str) -> FermentableDetail:
        url = self._build_url(
            f"inventory/{InventoryCategory.FERMENTABLES}", id=id
        )
        json_response = await self._make_request(url)
        return FermentableDetail.model_validate_json(json_response)

    async def update_fermentable_inventory(self, id: str, inventory: float) -> None:
        url = self._build_url(
            f"inventory/{InventoryCategory.FERMENTABLES}", id=id
        )
        await self._make_patch_request(url, {"inventory": inventory})

    # Batch endpoints
    async def get_batches_list(
        self, query_params: ListQueryParams | None = None
    ) -> BatchList:
        return await self._get_paginated_list("batches", BatchList, query_params)

    async def get_batch_detail(self, id: str) -> BatchDetail:
        url = self._build_url("batches", id=id)
        json_response = await self._make_request(url)
        return BatchDetail.model_validate_json(json_response)

    async def update_batch_detail(self, id: str, data: dict) -> None:
        url = self._build_url("batches", id=id)
        await self._make_patch_request(url, data)

    # Recipe endpoints
    async def get_recipes_list(
        self, query_params: ListQueryParams | None = None
    ) -> RecipeList:
        return await self._get_paginated_list("recipes", RecipeList, query_params)

    async def get_recipe_detail(self, id: str) -> RecipeDetail:
        url = self._build_url("recipes", id=id)
        json_response = await self._make_request(url)
        return RecipeDetail.model_validate_json(json_response)

    # Add similar patterns for other inventory types (hops, yeasts, miscs)...
    async def get_hops_list(
        self, query_params: ListQueryParams | None = None
    ) -> HopList:
        return await self._get_paginated_list(
            f"inventory/{InventoryCategory.HOPS}",
            HopList,
            query_params
        )
    
    async def get_hop_detail(self, id: str) -> HopDetail:
        url = self._build_url(
            f"inventory/{InventoryCategory.HOPS}", id=id
        )
        json_response = await self._make_request(url)
        return HopDetail.model_validate_json(json_response)
    
    async def update_hop_inventory(self, id: str, inventory: float) -> None:
        url = self._build_url(
            f"inventory/{InventoryCategory.HOPS}", id=id
        )
        await self._make_patch_request(url, {"inventory": inventory})

    async def get_yeasts_list(
        self, query_params: ListQueryParams | None = None
    ) -> YeastList:
        return await self._get_paginated_list(
            f"inventory/{InventoryCategory.YEASTS}",
            YeastList,
            query_params
        )
    
    async def get_yeast_detail(self, id: str) -> YeastDetail:
        url = self._build_url(
            f"inventory/{InventoryCategory.YEASTS}", id=id
        )
        json_response = await self._make_request(url)
        return YeastDetail.model_validate_json(json_response)
    
    async def update_yeast_inventory(self, id: str, inventory: float) -> None:
        url = self._build_url(
            f"inventory/{InventoryCategory.YEASTS}", id=id
        )
        await self._make_patch_request(url, {"inventory": inventory})

    async def get_miscs_list(
        self, query_params: ListQueryParams | None = None
    ) -> MiscList:
        return await self._get_paginated_list(
            f"inventory/{InventoryCategory.MISCS}",
            MiscList,
            query_params
        )

    async def get_misc_detail(self, id: str) -> MiscDetail:
        url = self._build_url(
            f"inventory/{InventoryCategory.MISCS}", id=id
        )
        json_response = await self._make_request(url)
        return MiscDetail.model_validate_json(json_response)
    
    async def update_misc_inventory(self, id: str, inventory: float) -> None:
        url = self._build_url(
            f"inventory/{InventoryCategory.MISCS}", id=id
        )
        await self._make_patch_request(url, {"inventory": inventory})

    # Brewtracker endpoints
    async def get_batch_brewtracker(self, batch_id: str) -> BrewTrackerStatus:
        """Get brewtracker status for a batch"""
        url = self._build_url("batches", id=f"{batch_id}/brewtracker")
        json_response = await self._make_request(url)
        return BrewTrackerStatus.model_validate_json(json_response)
    
    async def get_batch_readings(self, batch_id: str) -> BatchReadingsList:
        """Get all readings for a batch"""
        url = self._build_url("batches", id=f"{batch_id}/readings")
        json_response = await self._make_request(url)
        return BatchReadingsList.model_validate_json(json_response)
    
    async def get_batch_last_reading(self, batch_id: str) -> LastReading:
        """Get last reading for a batch"""
        url = self._build_url("batches", id=f"{batch_id}/readings/last")
        json_response = await self._make_request(url)
        return LastReading.model_validate_json(json_response)
