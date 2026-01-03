"""Detail tools for getting full entity information.

Returns raw JSON for Claude to process.
Rate limited: 100 requests/day for detail endpoints.
"""

import json
from mcp_server.api_client import client


async def get_company_details(cin: str) -> str:
    """Get full company details by CIN. Rate limited: 100/day."""
    result = await client.get("/company/details", params={"cin": cin})
    return json.dumps(result, indent=2, default=str)


async def get_director_details(din: str) -> str:
    """Get full director details by DIN. Rate limited: 100/day."""
    result = await client.get("/company/director-details", params={"din": din})
    return json.dumps(result, indent=2, default=str)


async def get_gst_details(gstin: str) -> str:
    """Get full GST registration details by GSTIN. Rate limited: 100/day."""
    result = await client.get("/gst/details", params={"gstin": gstin})
    return json.dumps(result, indent=2, default=str)
