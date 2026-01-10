"""Finscreener MCP Server - Main Entry Point.

An MCP server that exposes Finscreener APIs for company, director, and GST data
access from AI agents like Claude Desktop.

Usage:
    # Run with stdio transport (for Claude Desktop)
    python -m mcp_server.server
    
    # Or via uv
    uv run server.py
"""

import os
import logging
from typing import Optional, List

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "finscreener",
    dependencies=["httpx", "python-dotenv"]
)

# Import tool implementations
from mcp_server.tools.search_tools import (
    search_company as _search_company,
    search_director as _search_director,
    search_gst as _search_gst,
)
from mcp_server.tools.detail_tools import (
    get_company_details as _get_company_details,
    get_director_details as _get_director_details,
    get_gst_details as _get_gst_details,
)
from mcp_server.tools.watchlist_tools import (
    list_watchlists as _list_watchlists,
    get_watchlist_details as _get_watchlist_details,
    create_watchlist as _create_watchlist,
    delete_watchlist as _delete_watchlist,
)
from mcp_server.tools.screener_tools import (
    run_screener as _run_screener,
    create_screener as _create_screener,
    list_screeners as _list_screeners,
    get_screener as _get_screener,
    update_screener as _update_screener,
    delete_screener as _delete_screener,
    screener_to_watchlist as _screener_to_watchlist,
    screener_to_order as _screener_to_order,
)
from mcp_server.tools.order_tools import (
    list_orders as _list_orders,
    get_order_details as _get_order_details,
    create_order as _create_order,
    watchlist_to_order as _watchlist_to_order,
    get_user_credits as _get_user_credits,
)
from mcp_server.tools.classification_tools import (
    lookup_nic_code as _lookup_nic_code,
    lookup_hsn_code as _lookup_hsn_code,
    lookup_sac_code as _lookup_sac_code,
)
from mcp_server.tools.crm_tools import (
    list_crm_orders as _list_crm_orders,
    get_order_leads as _get_order_leads,
    get_entity_as_lead as _get_entity_as_lead,
)


# ============================================================================
# Search Tools
# ============================================================================

@mcp.tool()
async def search_company(query: str) -> str:
    """Search for companies by name to get CIN (Corporate Identification Number).

    NOTE: Name search can be slow on large datasets.
    For faster industry-based search, use run_screener instead:
    1. lookup_nic_code(search="software") → get NIC codes
    2. run_screener(query="NICCode IN [62011, 62012] AND City == 'Mumbai'", type="company")

    Args:
        query: Company name fragment or CIN (21-char CIN is faster)
    """
    return await _search_company(query)


@mcp.tool()
async def search_director(query: str) -> str:
    """Search for directors by name to get DIN (Director Identification Number).
    
    Use this when you need to find a director's DIN from their name.
    
    Args:
        query: Director name fragment or DIN snippet to search for
    """
    return await _search_director(query)


@mcp.tool()
async def search_gst(query: str) -> str:
    """Search for GST registrations by business name to get GSTIN.
    
    Use this when you need to find a business's GSTIN from its trade name.
    
    Args:
        query: Trade name fragment or GSTIN snippet to search for
    """
    return await _search_gst(query)


# ============================================================================
# Detail Tools
# ============================================================================

@mcp.tool()
async def get_company_details(cin: str) -> str:
    """Get detailed information about a company using its CIN.
    
    Returns incorporation date, capital, status, registered address, directors, etc.
    
    Args:
        cin: Corporate Identification Number (CIN) of the company
    """
    return await _get_company_details(cin)


@mcp.tool()
async def get_director_details(din: str) -> str:
    """Get detailed information about a director using their DIN.
    
    Returns director profile, disqualification status, and associated companies.
    
    Args:
        din: Director Identification Number (DIN) of the director
    """
    return await _get_director_details(din)


@mcp.tool()
async def get_gst_details(gstin: str) -> str:
    """Get detailed GST registration information using GSTIN.
    
    Returns status, taxpayer type, registration date, address, etc.
    
    Args:
        gstin: 15-character GST Identification Number (GSTIN)
    """
    return await _get_gst_details(gstin)


# ============================================================================
# Watchlist Tools
# ============================================================================

@mcp.tool()
async def list_watchlists() -> str:
    """List all watchlists owned by the current user.
    
    Returns list of watchlists with id, name, type, and item count.
    """
    return await _list_watchlists()


@mcp.tool()
async def get_watchlist_details(
    watchlist_id: str,
    page: int = 1,
    limit: int = 10,
    search_query: Optional[str] = None
) -> str:
    """Get the contents of a specific watchlist.
    
    Args:
        watchlist_id: ID of the watchlist to inspect
        page: Page number for pagination (default 1)
        limit: Items per page (default 10)
        search_query: Optional text filter for entity name/identifier
    """
    return await _get_watchlist_details(watchlist_id, page, limit, search_query)


@mcp.tool()
async def create_watchlist(
    name: str,
    watchlist_type: str,
    items: Optional[List[dict]] = None
) -> str:
    """Create a new watchlist to track companies, directors, or GST registrations.
    
    Args:
        name: Display name for the watchlist
        watchlist_type: Type of entities - "company", "director", or "gst"
        items: Optional list of entities to add, each with "number" (CIN/DIN/GSTIN) and "name"
    """
    return await _create_watchlist(name, watchlist_type, items)


@mcp.tool()
async def delete_watchlist(watchlist_id: str) -> str:
    """Delete a watchlist.
    
    Args:
        watchlist_id: ID of the watchlist to delete
    """
    return await _delete_watchlist(watchlist_id)


# ============================================================================
# Screener Tools
# ============================================================================

@mcp.tool()
async def run_screener(
    query: str,
    type: str,
    page: int = 1,
    limit: int = 10
) -> str:
    """Execute an FQL query to filter companies or GST registrations.

    IMPORTANT: Field names are case-sensitive!

    Company fields: City, State, paidUpCapital, NICCode, mainDivision, llpStatus, Listed, dateOfIncorporation
    GST fields: state (lowercase!), Status, saccd, hsncd, ConstitutionBusiness, BusinessActivities, Turnover

    For industry search: Use lookup_nic_code first to get codes, then use NICCode IN [codes]

    FQL examples:
    - City == 'Mumbai' AND paidUpCapital > 10000000
    - State == 'Maharashtra' AND llpStatus == 'Active'
    - NICCode IN [62011, 62012, 62020] AND City == 'Bangalore'
    - mainDivision == '62' AND paidUpCapital > 50000000
    - state == 'Gujarat' AND Status == 'Active' (GST)
    - saccd IN [999612, 999614] AND state == 'Maharashtra' (GST)

    Args:
        query: FQL query string (case-sensitive field names!)
        type: "company" or "gst"
        page: Page number (default 1)
        limit: Results per page (default 10, max 100)
    """
    return await _run_screener(query, type, page, limit)


@mcp.tool()
async def create_screener(
    name: str,
    query: str,
    type: str,
    description: Optional[str] = None
) -> str:
    """Save an FQL query as a reusable screener.
    
    Args:
        name: Display name for the screener
        query: FQL query string to save
        type: Type of entities - "company" or "gst"
        description: Optional description of what this screener finds
    """
    return await _create_screener(name, query, type, description)


@mcp.tool()
async def list_screeners() -> str:
    """List all saved screeners owned by the current user."""
    return await _list_screeners()


@mcp.tool()
async def get_screener(screener_id: str) -> str:
    """Get a saved screener by ID.
    
    Args:
        screener_id: ID of the screener to fetch
    """
    return await _get_screener(screener_id)


@mcp.tool()
async def update_screener(
    screener_id: str,
    name: Optional[str] = None,
    query: Optional[str] = None,
    type: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """Update an existing screener's properties.
    
    Args:
        screener_id: ID of the screener to update
        name: New name (optional)
        query: New FQL query (optional)
        type: New entity type (optional)
        description: New description (optional)
    """
    return await _update_screener(screener_id, name, query, type, description)


@mcp.tool()
async def delete_screener(screener_id: str) -> str:
    """Delete a saved screener.
    
    Args:
        screener_id: ID of the screener to delete
    """
    return await _delete_screener(screener_id)


@mcp.tool()
async def screener_to_watchlist(
    watchlist_name: str,
    watchlist_type: str,
    query: str,
    limit: int = 100
) -> str:
    """Convert screener results into a watchlist for monitoring.

    Args:
        watchlist_name: Name for the new watchlist
        watchlist_type: Type - "company", "director", or "gst"
        query: FQL query to execute
        limit: Maximum entities to add (default 100)
    """
    return await _screener_to_watchlist(watchlist_name, watchlist_type, query, limit)


@mcp.tool()
async def screener_to_order(
    order_name: str,
    payment_option: str,
    query: Optional[str] = None,
    screener_id: Optional[str] = None,
    type: Optional[str] = None,
    limit: Optional[int] = None
) -> str:
    """Create an order from screener results to purchase detailed data.
    
    Provide either query or screener_id. Use limit to specify how many top results.
    
    Args:
        order_name: Name for the order
        payment_option: "credits" (use credits) or "paylater" (pay later)
        query: FQL query to execute (if not using screener_id)
        screener_id: ID of saved screener (if not using query)
        type: Entity type when using query - "company", "director", or "gst"
        limit: Maximum items to include (e.g., top 50)
    """
    return await _screener_to_order(order_name, payment_option, query, screener_id, type, limit)


# ============================================================================
# Order Tools
# ============================================================================

@mcp.tool()
async def list_orders(
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> str:
    """List user's orders with optional filters.

    Args:
        page: Page number (default 1)
        limit: Orders per page (default 10)
        status: Filter by order status
        search: Search in order ID or name
    """
    return await _list_orders(page, limit, status, search)


@mcp.tool()
async def get_order_details(order_id: str) -> str:
    """Get full details for a specific order.

    Args:
        order_id: ID of the order to fetch
    """
    return await _get_order_details(order_id)


@mcp.tool()
async def create_order(
    order_name: str,
    payment_option: str,
    items: List[dict]
) -> str:
    """Create a new order for contacts/registrations.

    Order Types & Credit Pricing:
    - company: Company contact data (1 credit)
    - director: Director contact data (1 credit)
    - gst: GST registration contact data (1 credit)
    - fullcompany: Full company + all directors + GST (5 credits)

    Args:
        order_name: Name describing the order
        payment_option: "credits" or "paylater"
        items: List of items with "type", "name", and "number" (CIN/DIN/GSTIN)
    """
    return await _create_order(order_name, payment_option, items)


@mcp.tool()
async def watchlist_to_order(
    watchlist_id: str,
    order_name: str,
    payment_option: str
) -> str:
    """Create an order from watchlist items.

    Args:
        watchlist_id: ID of the watchlist to convert
        order_name: Name for the order
        payment_option: "credits" or "paylater"
    """
    return await _watchlist_to_order(watchlist_id, order_name, payment_option)


@mcp.tool()
async def get_user_credits() -> str:
    """Check user's credit balance. Call this before creating orders with credits."""
    return await _get_user_credits()


# ============================================================================
# CRM Integration Tools
# ============================================================================

@mcp.tool()
async def list_crm_orders(
    page: int = 1,
    limit: int = 20
) -> str:
    """List orders available for CRM integration (Zoho export).

    Returns orders that can be exported as Zoho-ready leads.

    Args:
        page: Page number (default 1)
        limit: Orders per page (default 20, max 100)
    """
    return await _list_crm_orders(page, limit)


@mcp.tool()
async def get_order_leads(order_id: str) -> str:
    """Get order items as Zoho-ready leads for CRM import.

    Returns enriched lead data with:
    - For company/director/gst: 'lead' (Zoho format) and 'full_data'
    - For fullcompany: Flattened data with 'directors' and 'gst' arrays

    Directors include email and mobile from contact data.
    Order must be paid to access lead data.

    Args:
        order_id: ID of the order to get leads for
    """
    return await _get_order_leads(order_id)


@mcp.tool()
async def get_entity_as_lead(
    entity_type: str,
    identifier: str
) -> str:
    """Preview an entity as Zoho-ready lead format.

    Use this to see how an entity will appear as a Zoho lead
    before creating an order.

    Entity Types:
    - company: Company data (requires CIN)
    - director: Director data (requires DIN)
    - gst: GST registration data (requires GSTIN)
    - fullcompany: Company + all directors + GST (requires CIN)

    Args:
        entity_type: "company", "director", "gst", or "fullcompany"
        identifier: CIN, DIN, or GSTIN
    """
    return await _get_entity_as_lead(entity_type, identifier)


# ============================================================================
# Classification Tools
# ============================================================================

@mcp.tool()
async def lookup_nic_code(
    code: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 10
) -> str:
    """Lookup NIC (National Industrial Classification) codes.
    
    Use to understand industry classifications in company data.
    
    Args:
        code: Exact NIC code (e.g., "35101" or "3510" for partial)
        search: Keyword to search (e.g., "software", "manufacturing")
        limit: Maximum results (default 10)
    """
    return await _lookup_nic_code(code, search, limit)


@mcp.tool()
async def lookup_hsn_code(
    code: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 10
) -> str:
    """Lookup HSN (Harmonized System of Nomenclature) codes for goods/products.
    
    Use to understand product classifications in GST data.
    
    Args:
        code: Exact HSN code (e.g., "01011010" or "0101" for partial)
        search: Keyword to search (e.g., "horses", "textiles")
        limit: Maximum results (default 10)
    """
    return await _lookup_hsn_code(code, search, limit)


@mcp.tool()
async def lookup_sac_code(
    code: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 10
) -> str:
    """Lookup SAC (Services Accounting Code) codes for services.
    
    Use to understand service classifications in GST data.
    
    Args:
        code: Exact SAC code (e.g., "995411" or "9954" for partial)
        search: Keyword to search (e.g., "construction", "consulting")
        limit: Maximum results (default 10)
    """
    return await _lookup_sac_code(code, search, limit)


# ============================================================================
# MCP Resources (Read-only static information)
# ============================================================================

@mcp.resource("finscreener://guide/fql")
def get_fql_guide() -> str:
    """FQL (FinScreener Query Language) syntax guide."""
    return """
# FQL - FinScreener Query Language Guide

## Operators
- `==` (equals), `!=` (not equals)
- `>` (greater than), `<` (less than), `>=`, `<=`
- `IN` - match any from list: `field IN ['value1', 'value2']`
- `NOT IN` - exclude values
- `AND`, `OR` - combine conditions
- `( )` - group conditions

## Company Fields (EXACT NAMES - Case Sensitive!)
| Field | Description | Example |
|-------|-------------|---------|
| `CIN` | Corporate ID | `CIN == 'U12345MH2020PTC123456'` |
| `company` | Company name | `company CONTAINS 'Infosys'` |
| `City` | City (uppercase C!) | `City == 'Mumbai'` |
| `State` | State name | `State == 'Maharashtra'` |
| `District` | District | `District == 'Mumbai Suburban'` |
| `Pincode` | 6-digit pincode | `Pincode == 400001` |
| `paidUpCapital` | Paid-up capital (INR) | `paidUpCapital > 10000000` |
| `authorizedCapital` | Authorized capital | `authorizedCapital > 50000000` |
| `NICCode` | 5-digit industry code | `NICCode IN [62011, 62012, 62020]` |
| `mainDivision` | 2-digit NIC division | `mainDivision == '62'` |
| `companyType` | Type | `companyType == 'Private'` |
| `classOfCompany` | Class | `classOfCompany == 'Private'` |
| `llpStatus` | Status | `llpStatus == 'Active'` |
| `Listed` | Listed/Unlisted | `Listed == 'Listed'` |
| `dateOfIncorporation` | Date (YYYY-MM-DD) | `dateOfIncorporation > '2020-01-01'` |

## GST Fields (EXACT NAMES - Case Sensitive!)
| Field | Description | Example |
|-------|-------------|---------|
| `GSTIN` | 15-char GST number | `GSTIN == '27AABCU9603R1ZM'` |
| `TradeName` | Trade name | `TradeName CONTAINS 'Tech'` |
| `LegalName` | Legal name | |
| `Status` | Status | `Status == 'Active'` |
| `state` | State (lowercase!) | `state == 'Maharashtra'` |
| `district` | District | `district == 'Mumbai'` |
| `TaxpayerType` | Taxpayer type | `TaxpayerType == 'Regular'` |
| `ConstitutionBusiness` | Business type | `ConstitutionBusiness == 'Private Limited'` |
| `BusinessActivities` | Activity type | `BusinessActivities == 'Factory / Manufacturing'` |
| `saccd` | SAC service codes | `saccd IN [999612, 999614]` |
| `hsncd` | HSN goods codes | `hsncd IN [5007, 5111]` |
| `Turnover` | Turnover | `Turnover > 10000000` |

## Industry Search (BEST PRACTICE)
**NEVER use CONTAINS on descriptions - it's SLOW!**
**ALWAYS lookup codes first, then use IN operator - it's FAST!**

1. Use `lookup_nic_code` to find industry codes
2. Use codes with `NICCode IN [...]`

Example for "tech companies in Mumbai":
```
NICCode IN [62011, 62012, 62020, 46512] AND City == 'Mumbai'
```

Common NIC divisions:
- 62 = IT/Software
- 46 = Wholesale
- 47 = Retail
- 10 = Food manufacturing
- 13 = Textiles

## Examples

### Company Queries
```
City == 'Mumbai' AND paidUpCapital > 10000000
State == 'Karnataka' AND llpStatus == 'Active'
NICCode IN [62011, 62012] AND City == 'Bangalore'
mainDivision == '62' AND paidUpCapital > 50000000
Listed == 'Listed' AND State == 'Maharashtra'
dateOfIncorporation > '2023-01-01' AND llpStatus == 'Active'
```

### GST Queries
```
state == 'Maharashtra' AND Status == 'Active'
saccd IN [999612, 999614] AND state == 'Maharashtra'
ConstitutionBusiness == 'Individual' AND state == 'Gujarat'
BusinessActivities == 'Export' AND state == 'Tamil Nadu'
hsncd IN [5007, 5111] AND BusinessActivities == 'Factory / Manufacturing'
```
"""


@mcp.resource("finscreener://about")
def get_about() -> str:
    """About Finscreener and available data."""
    return """
# About Finscreener

Finscreener provides comprehensive access to Indian business data:

## Data Available
- **MCA Data**: Company registrations (CIN), director details (DIN)
- **GST Data**: GST registrations (GSTIN), taxpayer information
- **Classifications**: NIC, HSN, SAC codes

## Key Features
- Search companies, directors, and GST registrations
- Run custom queries using FQL (FinScreener Query Language)
- Save queries as reusable screeners
- Create watchlists to monitor entities
- Order detailed contact information

## Authentication
Configure your API key in environment variables:
- FINSCREENER_API_KEY: Your API key (starts with fsk_)
- FINSCREENER_API_BASE: API base URL (default: https://api.finscreener.in)
"""


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the MCP server."""
    logger.info("Starting Finscreener MCP Server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
