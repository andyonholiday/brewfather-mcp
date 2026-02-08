import logging

from brewfather_mcp.api import BrewfatherClient, ListQueryParams
from brewfather_mcp.utils import AnyDictList

logger = logging.getLogger(__name__)


async def get_fermentables_summary(
    brewfather_client: BrewfatherClient,
) -> AnyDictList:
    """Get a summary of fermentable inventory items using only list data.

    Uses paginated list endpoint to fetch all items without requiring
    individual detail API calls, avoiding rate limit and timeout issues.
    """
    params = ListQueryParams()
    params.inventory_exists = True
    fermentables_data = await brewfather_client.get_fermentables_list(params)

    logger.info(f"Fetched {len(fermentables_data.root)} fermentables from paginated list")

    fermentables: AnyDictList = []
    for f_data in fermentables_data.root:
        fermentables.append(
            {
                "Name": f_data.name,
                "Type": f_data.type,
                "Supplier": f_data.supplier or "N/A",
                "Inventory Amount": f"{f_data.inventory} kg",
            }
        )

    return fermentables


async def get_hops_summary(brewfather_client: BrewfatherClient) -> AnyDictList:
    """Get a summary of hop inventory items using only list data.

    Uses paginated list endpoint to fetch all items without requiring
    individual detail API calls, avoiding rate limit and timeout issues.
    """
    params = ListQueryParams()
    params.inventory_exists = True
    hops_data = await brewfather_client.get_hops_list(params)

    logger.info(f"Fetched {len(hops_data.root)} hops from paginated list")

    hops: AnyDictList = []
    for h_data in hops_data.root:
        hops.append(
            {
                "Name": h_data.name,
                "Alpha Acid": h_data.alpha,
                "Type": h_data.type,
                "Use": h_data.use or "N/A",
                "Inventory Amount": f"{h_data.inventory} grams",
            }
        )

    return hops


async def get_yeast_summary(
    brewfather_client: BrewfatherClient,
) -> AnyDictList:
    """Get a summary of yeast inventory items using only list data.

    Uses paginated list endpoint to fetch all items without requiring
    individual detail API calls, avoiding rate limit and timeout issues.
    """
    params = ListQueryParams()
    params.inventory_exists = True
    yeasts_data = await brewfather_client.get_yeasts_list(params)

    logger.info(f"Fetched {len(yeasts_data.root)} yeasts from paginated list")

    yeasts: AnyDictList = []
    for y_data in yeasts_data.root:
        yeasts.append(
            {
                "Name": y_data.name,
                "Type": y_data.type,
                "Attenuation": f"{y_data.attenuation}%",
                "Inventory Amount": f"{y_data.inventory} pkg",
            }
        )

    return yeasts


async def get_miscs_summary(
    brewfather_client: BrewfatherClient,
) -> AnyDictList:
    """Get a summary of miscellaneous inventory items using only list data.

    Uses paginated list endpoint to fetch all items without requiring
    individual detail API calls, avoiding rate limit and timeout issues.

    Args:
        brewfather_client: The Brewfather API client instance.

    Returns:
        A list of dictionaries containing summarized miscellaneous item information.
    """
    params = ListQueryParams()
    params.inventory_exists = True
    miscs_data = await brewfather_client.get_miscs_list(params)

    logger.info(f"Fetched {len(miscs_data.root)} misc items from paginated list")

    miscs: AnyDictList = []
    for m_data in miscs_data.root:
        miscs.append(
            {
                "Name": m_data.name,
                "Type": m_data.type or "N/A",
                "Notes": m_data.notes or "N/A",
                "Inventory Amount": f"{m_data.inventory} units",
            }
        )

    return miscs
