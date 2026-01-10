"""CRM Integration tools for exporting order data as Zoho-ready leads.

These tools use the Developer API CRM endpoints for exporting data
in Zoho CRM lead format.

Endpoints:
- GET /api/crm/orders - List orders for CRM integration
- GET /api/crm/orders/{id}/leads - Get order items as Zoho-ready leads
- POST /api/crm/newlead - Get entity as Zoho lead format (preview)
"""

import json
from typing import Optional
from mcp_server.api_client import client


async def list_crm_orders(
    page: int = 1,
    limit: int = 20
) -> str:
    """List orders available for CRM integration.

    Returns orders that can be exported as Zoho-ready leads.

    Args:
        page: Page number (default 1)
        limit: Orders per page (default 20, max 100)
    """
    params = {"page": page, "limit": limit}
    result = await client.get("/crm/orders", params=params)
    return json.dumps(result, indent=2, default=str)


async def get_order_leads(order_id: str) -> str:
    """Get order items as Zoho-ready leads.

    Returns enriched lead data with:
    - For company/director/gst types: 'lead' (Zoho format) and 'full_data'
    - For fullcompany type: Flattened company data with 'directors' and 'gst' arrays

    Note: Order must be paid to access lead data.

    Args:
        order_id: ID of the order to get leads for
    """
    result = await client.get(f"/crm/orders/{order_id}/leads")
    return json.dumps(result, indent=2, default=str)


async def get_entity_as_lead(
    entity_type: str,
    identifier: str
) -> str:
    """Get an entity as Zoho-ready lead format (preview).

    Use this to preview how an entity will appear as a Zoho lead
    before creating an order.

    Entity Types:
    - company: Company data (requires CIN)
    - director: Director data (requires DIN)
    - gst: GST registration data (requires GSTIN)
    - fullcompany: Company + all directors + GST (requires CIN)

    Note: Requires active subscription with access to recently registered data.

    Args:
        entity_type: Type of entity - "company", "director", "gst", or "fullcompany"
        identifier: CIN, DIN, or GSTIN
    """
    valid_types = ["company", "director", "gst", "fullcompany"]
    if entity_type not in valid_types:
        return json.dumps({"error": f"Invalid entity_type '{entity_type}'. Must be one of: {valid_types}"})

    if not identifier:
        return json.dumps({"error": "identifier is required (CIN, DIN, or GSTIN)"})

    payload = {
        "entity_type": entity_type,
        "identifier": identifier
    }

    result = await client.post("/crm/newlead", json_data=payload)
    return json.dumps(result, indent=2, default=str)
