"""Order management tools for creating and tracking orders.

These tools use the Developer API order endpoints for managing orders.
Returns raw JSON for Claude to process.

Order Types:
- company: Company contact data (1 credit)
- director: Director contact data (1 credit)
- gst: GST registration contact data (1 credit)
- fullcompany: Full company data with all directors and GST (5 credits)
"""

import json
from typing import Optional, List
from mcp_server.api_client import client

# Credit pricing per order type
CREDIT_PRICES = {
    "company": 1,
    "director": 1,
    "gst": 1,
    "fullcompany": 5
}

VALID_ORDER_TYPES = ["company", "director", "gst", "fullcompany"]


async def list_orders(
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> str:
    """List all orders for the current user."""
    params = {"page": page, "limit": limit}
    if status:
        params["status"] = status
    if search:
        params["search"] = search

    result = await client.get("/orders", params=params)
    return json.dumps(result, indent=2, default=str)


async def get_order_details(order_id: str) -> str:
    """Get detailed information about a specific order including contact data."""
    result = await client.get(f"/orders/{order_id}")
    return json.dumps(result, indent=2, default=str)


async def create_order(
    order_name: str,
    payment_option: str,
    items: List[dict]
) -> str:
    """Create a new order for contact data.

    Args:
        order_name: Name/description for this order
        payment_option: "credits" or "cashfree"
        items: List of items with type, name, number, price
               Types: company (1 credit), director (1 credit), gst (1 credit), fullcompany (5 credits)
               For fullcompany: Returns company + all directors + GST data
    """
    if payment_option not in ["credits", "cashfree"]:
        return json.dumps({"error": f"Invalid payment_option '{payment_option}'. Must be 'credits' or 'cashfree'."})

    if not items or len(items) == 0:
        return json.dumps({"error": "At least one item is required to create an order."})

    validated_items = []
    for i, item in enumerate(items):
        item_type = item.get("type")
        if not item_type or item_type not in VALID_ORDER_TYPES:
            return json.dumps({"error": f"Item {i+1} has invalid type '{item_type}'. Must be one of: {VALID_ORDER_TYPES}"})
        if not item.get("number"):
            return json.dumps({"error": f"Item {i+1} is missing 'number' (CIN/DIN/GSTIN)."})

        # Use correct credit price for the type
        price = CREDIT_PRICES.get(item_type, 1)

        validated_items.append({
            "type": item_type,
            "name": item.get("name", item["number"]),
            "number": item["number"],
            "price": float(item.get("price", price))
        })

    payload = {
        "orderName": order_name,
        "paymentOption": payment_option,
        "items": validated_items
    }

    result = await client.post("/orders/normal", json_data=payload)
    return json.dumps(result, indent=2, default=str)


async def watchlist_to_order(
    watchlist_id: str,
    order_name: str,
    payment_option: str
) -> str:
    """Create an order from all entities in a watchlist."""
    if payment_option not in ["credits", "cashfree"]:
        return json.dumps({"error": f"Invalid payment_option '{payment_option}'. Must be 'credits' or 'cashfree'."})

    # Get watchlist using Developer API
    wl_result = await client.get(f"/watchlist/{watchlist_id}")

    if isinstance(wl_result, dict) and wl_result.get("success") == False:
        return json.dumps(wl_result)

    wl_data = wl_result.get("data", wl_result) if isinstance(wl_result, dict) else wl_result
    items_data = wl_data.get("items", wl_data.get("entities", [])) if isinstance(wl_data, dict) else []

    if not items_data:
        return json.dumps({"error": "Watchlist is empty."})

    order_items = []
    for item in items_data:
        order_items.append({
            "type": item.get("type", "company"),
            "name": item.get("name", item.get("number", "Unknown")),
            "number": item.get("number", item.get("identifier", "")),
            "price": 10.0
        })

    return await create_order(order_name, payment_option, order_items)


async def get_user_credits() -> str:
    """Get the current user's credit balance."""
    result = await client.get("/users/me")
    return json.dumps(result, indent=2, default=str)
