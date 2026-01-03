"""Watchlist management tools.

Returns raw JSON for Claude to process.
"""

import json
from typing import List, Optional
from mcp_server.api_client import client


async def list_watchlists() -> str:
    """List all watchlists owned by the current user."""
    result = await client.get("/watchlist")
    return json.dumps(result, indent=2, default=str)


async def get_watchlist_details(
    watchlist_id: str,
    page: int = 1,
    limit: int = 10,
    search_query: Optional[str] = None
) -> str:
    """Get the contents of a specific watchlist."""
    params = {"page": page, "limit": limit}
    if search_query:
        params["search_query"] = search_query

    result = await client.get(f"/watchlist/{watchlist_id}/entities", params=params)
    return json.dumps(result, indent=2, default=str)


async def create_watchlist(
    name: str,
    watchlist_type: str,
    items: Optional[List[dict]] = None
) -> str:
    """Create a new watchlist with optional initial entities.

    Args:
        name: Display name for the watchlist
        watchlist_type: "company", "director", or "gst"
        items: Optional list of entities with "number" and "name"
    """
    if watchlist_type not in ["company", "director", "gst"]:
        return json.dumps({"error": f"Invalid watchlist type '{watchlist_type}'. Must be 'company', 'director', or 'gst'."})

    payload = {
        "name": name,
        "watchlist_type": watchlist_type,
    }

    if items:
        payload["entities"] = [
            {"identifier": item.get("number", item.get("identifier")), "name": item.get("name")}
            for item in items
        ]

    result = await client.post("/watchlist", json_data=payload)
    return json.dumps(result, indent=2, default=str)


async def delete_watchlist(watchlist_id: str) -> str:
    """Delete a watchlist."""
    result = await client.delete(f"/watchlist/{watchlist_id}")
    return json.dumps(result, indent=2, default=str)
