"""Classification lookup tools for NIC, HSN, and SAC codes.

Returns raw JSON for Claude to process.
"""

import json
from typing import Optional
from mcp_server.api_client import client


async def lookup_nic_code(
    code: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 10
) -> str:
    """Lookup NIC (National Industrial Classification) codes.

    Use codes with NICCode IN [...] in screener queries for fast industry search.

    Args:
        code: Exact NIC code (e.g., "62011")
        search: Keyword to search (e.g., "software", "manufacturing")
        limit: Maximum results (default 10, max 50)
    """
    if not code and not search:
        return json.dumps({"error": "Provide either 'code' or 'search' parameter."})

    params = {"limit": min(limit, 50)}
    if code:
        params["code"] = code
    if search:
        params["search"] = search

    result = await client.get("/reference/nic", params=params)
    return json.dumps(result, indent=2, default=str)


async def lookup_hsn_code(
    code: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 10
) -> str:
    """Lookup HSN (Harmonized System) codes for goods/products.

    Use codes with hsncd IN [...] in GST screener queries.

    Args:
        code: Exact HSN code (e.g., "5007")
        search: Keyword to search (e.g., "textile", "chemical")
        limit: Maximum results (default 10, max 50)
    """
    if not code and not search:
        return json.dumps({"error": "Provide either 'code' or 'search' parameter."})

    params = {"limit": min(limit, 50)}
    if code:
        params["code"] = code
    if search:
        params["search"] = search

    result = await client.get("/reference/hsn", params=params)
    return json.dumps(result, indent=2, default=str)


async def lookup_sac_code(
    code: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 10
) -> str:
    """Lookup SAC (Services Accounting Code) codes for services.

    Use codes with saccd IN [...] in GST screener queries.

    Args:
        code: Exact SAC code (e.g., "999612")
        search: Keyword to search (e.g., "film", "software")
        limit: Maximum results (default 10, max 50)
    """
    if not code and not search:
        return json.dumps({"error": "Provide either 'code' or 'search' parameter."})

    params = {"limit": min(limit, 50)}
    if code:
        params["code"] = code
    if search:
        params["search"] = search

    result = await client.get("/reference/sac", params=params)
    return json.dumps(result, indent=2, default=str)
