"""Screener tools for FQL queries and saved screeners.

Returns raw JSON for Claude to process.
IMPORTANT: Field names are CASE-SENSITIVE!

COMPANY FIELDS: City, State, paidUpCapital, NICCode, mainDivision, llpStatus, Listed
GST FIELDS: state (lowercase!), Status, saccd, hsncd, ConstitutionBusiness, BusinessActivities
"""

import json
from typing import Optional, List
from mcp_server.api_client import client


async def run_screener(
    query: str,
    type: str,
    page: int = 1,
    limit: int = 10
) -> str:
    """Execute FQL query. Field names are CASE-SENSITIVE!

    Examples:
    - City == 'Mumbai' AND paidUpCapital > 10000000
    - NICCode IN [62011, 62012] AND State == 'Maharashtra'
    - state == 'Gujarat' AND Status == 'Active' (GST)
    """
    if type not in ["company", "gst"]:
        return json.dumps({"error": f"Invalid type '{type}'. Must be 'company' or 'gst'."})

    result = await client.post(
        "/screener/search",
        json_data={"query": query, "type": type, "page": page, "limit": min(limit, 100)},
        timeout=240.0
    )
    return json.dumps(result, indent=2, default=str)


async def create_screener(
    name: str,
    query: str,
    type: str,
    description: Optional[str] = None
) -> str:
    """Save FQL query as reusable screener."""
    if type not in ["company", "gst"]:
        return json.dumps({"error": f"Invalid type '{type}'. Must be 'company' or 'gst'."})

    payload = {"name": name, "query": query, "type": type}
    if description:
        payload["description"] = description

    result = await client.post("/screener/screeners", json_data=payload)
    return json.dumps(result, indent=2, default=str)


async def list_screeners() -> str:
    """List all saved screeners."""
    result = await client.get("/screener/screeners")
    return json.dumps(result, indent=2, default=str)


async def get_screener(screener_id: str) -> str:
    """Get saved screener by ID."""
    result = await client.get(f"/screener/screeners/{screener_id}")
    return json.dumps(result, indent=2, default=str)


async def update_screener(
    screener_id: str,
    name: Optional[str] = None,
    query: Optional[str] = None,
    type: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """Update an existing screener."""
    existing = await client.get(f"/screener/screeners/{screener_id}")
    if isinstance(existing, dict) and existing.get("success") == False:
        return json.dumps(existing)

    data = existing.get("data", existing) if isinstance(existing, dict) else existing

    payload = {
        "name": name or data.get("name"),
        "query": query or data.get("query"),
        "type": type or data.get("type"),
    }
    if description or data.get("description"):
        payload["description"] = description or data.get("description")

    result = await client.put(f"/screener/screeners/{screener_id}", json_data=payload)
    return json.dumps(result, indent=2, default=str)


async def delete_screener(screener_id: str) -> str:
    """Delete a saved screener."""
    result = await client.delete(f"/screener/screeners/{screener_id}")
    return json.dumps(result, indent=2, default=str)


async def screener_to_watchlist(
    watchlist_name: str,
    watchlist_type: str,
    query: str,
    limit: int = 100
) -> str:
    """Convert screener results to watchlist."""
    if watchlist_type not in ["company", "director", "gst"]:
        return json.dumps({"error": f"Invalid type '{watchlist_type}'."})

    screener_type = "company" if watchlist_type in ["company", "director"] else "gst"
    result = await client.post(
        "/screener/search",
        json_data={"query": query, "type": screener_type, "page": 1, "limit": min(limit, 500)},
        timeout=240.0
    )

    if isinstance(result, dict) and result.get("success") == False:
        return json.dumps(result)

    data = result.get("results", result.get("data", result)) if isinstance(result, dict) else result

    if not isinstance(data, list) or not data:
        return json.dumps({"error": f"No results found for query: {query}"})

    entities = []
    for item in data[:limit]:
        if watchlist_type == "company":
            entities.append({
                "identifier": item.get("CIN", item.get("cin", "")),
                "name": item.get("company", item.get("companyName", "Unknown"))
            })
        elif watchlist_type == "director":
            entities.append({
                "identifier": item.get("DIN", item.get("din", "")),
                "name": item.get("directorName", item.get("name", "Unknown"))
            })
        else:
            entities.append({
                "identifier": item.get("GSTIN", item.get("gstin", "")),
                "name": item.get("TradeName", item.get("tradeName", item.get("LegalName", "Unknown")))
            })

    entities = [e for e in entities if e.get("identifier")]

    if not entities:
        return json.dumps({"error": "No valid entities found."})

    payload = {
        "name": watchlist_name,
        "watchlist_type": watchlist_type,
        "entities": entities
    }

    wl_result = await client.post("/watchlist", json_data=payload)
    return json.dumps(wl_result, indent=2, default=str)


async def screener_to_order(
    order_name: str,
    payment_option: str,
    query: Optional[str] = None,
    screener_id: Optional[str] = None,
    type: Optional[str] = None,
    limit: Optional[int] = None
) -> str:
    """Create order from screener results."""
    if payment_option not in ["credits", "cashfree", "paylater"]:
        return json.dumps({"error": f"Invalid payment_option '{payment_option}'."})

    if payment_option == "paylater":
        payment_option = "cashfree"

    if screener_id and not query:
        scr_result = await client.get(f"/screener/screeners/{screener_id}")
        if isinstance(scr_result, dict) and scr_result.get("success") == False:
            return json.dumps(scr_result)
        scr_data = scr_result.get("data", scr_result) if isinstance(scr_result, dict) else scr_result
        query = scr_data.get("query") if isinstance(scr_data, dict) else None
        type = scr_data.get("type") if isinstance(scr_data, dict) else type

    if not query:
        return json.dumps({"error": "Either query or screener_id required."})

    if not type or type not in ["company", "director", "gst"]:
        return json.dumps({"error": f"Invalid type '{type}'."})

    search_limit = limit or 100
    result = await client.post(
        "/screener/search",
        json_data={"query": query, "type": type, "page": 1, "limit": search_limit},
        timeout=240.0
    )

    if isinstance(result, dict) and result.get("success") == False:
        return json.dumps(result)

    data = result.get("results", result.get("data", result)) if isinstance(result, dict) else result

    if not isinstance(data, list) or not data:
        return json.dumps({"error": f"No results for query: {query}"})

    order_items = []
    for item in data[:search_limit]:
        if type == "company":
            order_items.append({
                "type": "company",
                "name": item.get("company", item.get("companyName", "Unknown")),
                "number": item.get("CIN", item.get("cin", "")),
                "price": 10.0
            })
        elif type == "director":
            order_items.append({
                "type": "director",
                "name": item.get("directorName", item.get("name", "Unknown")),
                "number": item.get("DIN", item.get("din", "")),
                "price": 10.0
            })
        else:
            order_items.append({
                "type": "gst",
                "name": item.get("TradeName", item.get("tradeName", item.get("LegalName", "Unknown"))),
                "number": item.get("GSTIN", item.get("gstin", "")),
                "price": 10.0
            })

    if not order_items:
        return json.dumps({"error": "No valid items for order."})

    payload = {
        "orderName": order_name,
        "paymentOption": payment_option,
        "items": order_items
    }

    order_result = await client.post("/orders/normal", json_data=payload)
    return json.dumps(order_result, indent=2, default=str)
