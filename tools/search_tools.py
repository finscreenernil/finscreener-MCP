"""Search tools for companies, directors, and GST registrations.

Returns raw JSON for Claude to process.
"""

import json
from typing import Optional
from mcp_server.api_client import client


async def search_company(
    query: str,
    state: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = 10
) -> str:
    """Search for companies by name or CIN.

    NOTE: Name search can be slow. For faster industry-based search, use run_screener:
    1. lookup_nic_code(search="software") to get NIC codes
    2. run_screener(query="NICCode IN [62011, 62012] AND City == 'Mumbai'", type="company")
    """
    params = {"page": 1, "limit": min(limit, 100)}

    if query and len(query) == 21 and query[0].isalpha():
        params["CIN"] = query
    else:
        params["company"] = query

    if state:
        params["state"] = state
    if city:
        params["city"] = city

    result = await client.get("/company/company-filter", params=params)
    return json.dumps(result, indent=2, default=str)


async def search_director(
    query: str,
    state: Optional[str] = None,
    limit: int = 10
) -> str:
    """Search for directors by name or DIN."""
    params = {"page": 1, "limit": min(limit, 100)}

    if query and query.isdigit() and len(query) == 8:
        params["DIN"] = query
    else:
        name_parts = query.strip().split() if query else []
        if len(name_parts) >= 2:
            params["firstName"] = name_parts[0]
            params["lastName"] = name_parts[-1]
        elif name_parts:
            params["firstName"] = name_parts[0]

    if state:
        params["state"] = state

    result = await client.get("/company/director-filter", params=params)
    return json.dumps(result, indent=2, default=str)


async def search_gst(
    query: str,
    state: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10
) -> str:
    """Search for GST registrations by trade name or GSTIN."""
    params = {"page": 1, "limit": min(limit, 100)}

    if query and len(query) == 15 and query[:2].isdigit():
        params["GSTIN"] = query
    else:
        params["TradeName"] = query

    if state:
        params["State"] = state
    if status:
        params["Status"] = status

    result = await client.get("/gst/gst-filter", params=params)
    return json.dumps(result, indent=2, default=str)
