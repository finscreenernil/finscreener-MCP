# Finscreener MCP Server

An MCP (Model Context Protocol) server that provides AI agents like Claude Desktop with access to Finscreener's company, director, and GST data through the Developer API.

**All tools return raw JSON responses** for Claude to process directly.

## Authentication

This MCP server uses **API Key authentication only**. No email/password or session-based auth.

1. Get your API key from Finscreener (starts with `fsk_`)
2. The server exchanges your API key for a JWT token automatically
3. All API calls use the Developer API (`/api/` endpoints)

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager (recommended)
- Finscreener API key (`fsk_xxx`)

### Installation

```bash
cd mcp_server

# Install dependencies
uv pip install -e .

# Or with pip
pip install -e .
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API key:
```bash
FINSCREENER_API_KEY=fsk_your_api_key_here
FINSCREENER_API_BASE=https://api.finscreener.in
```

### Claude Desktop Integration

Add to your Claude Desktop config:

**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "finscreener": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp_server",
        "run",
        "server.py"
      ],
      "env": {
        "FINSCREENER_API_KEY": "fsk_your_api_key_here",
        "FINSCREENER_API_BASE": "https://api.finscreener.in"
      }
    }
  }
}
```

Restart Claude Desktop after updating the config.

## Available Tools

### Search Tools
| Tool | Description |
|------|-------------|
| `search_company` | Search companies by name to get CIN |
| `search_director` | Search directors by name to get DIN |
| `search_gst` | Search GST registrations to get GSTIN |

### Detail Tools (Rate Limited: 100/day)
| Tool | Description |
|------|-------------|
| `get_company_details` | Get full company info by CIN |
| `get_director_details` | Get director profile by DIN |
| `get_gst_details` | Get GST registration details by GSTIN |

### Watchlist Tools
| Tool | Description |
|------|-------------|
| `list_watchlists` | List all your watchlists |
| `create_watchlist` | Create a new watchlist |
| `get_watchlist_details` | Get watchlist contents with pagination |
| `delete_watchlist` | Delete a watchlist |

### Screener Tools (FQL Queries)
| Tool | Description |
|------|-------------|
| `run_screener` | Execute an FQL query |
| `create_screener` | Save a query as reusable screener |
| `list_screeners` | List your saved screeners |
| `get_screener` | Get screener details by ID |
| `update_screener` | Update a screener |
| `delete_screener` | Delete a screener |
| `screener_to_watchlist` | Convert query results to watchlist |
| `screener_to_order` | Create order from query results |

### Order Tools
| Tool | Description |
|------|-------------|
| `list_orders` | List your orders |
| `create_order` | Create a new order (supports fullcompany type) |
| `get_order_details` | Get order details with contact data |
| `watchlist_to_order` | Create order from watchlist |
| `get_user_credits` | Check your credit balance |

**Order Types & Credit Pricing:**
| Type | Credits | Description |
|------|---------|-------------|
| `company` | 1 | Company contact data |
| `director` | 1 | Director contact data |
| `gst` | 1 | GST registration contact data |
| `fullcompany` | 5 | Full company + all directors + GST data |

### CRM Integration Tools
| Tool | Description |
|------|-------------|
| `list_crm_orders` | List orders for CRM/Zoho export |
| `get_order_leads` | Get order items as Zoho-ready leads |
| `get_entity_as_lead` | Preview entity as Zoho lead format |

**CRM Lead Format:**
- For `company`, `director`, `gst`: Returns `lead` (Zoho format) + `full_data`
- For `fullcompany`: Flattened data with `directors[]` and `gst` arrays, including email/mobile

### Classification Tools
| Tool | Description |
|------|-------------|
| `lookup_nic_code` | NIC (National Industrial Classification) lookup |
| `lookup_hsn_code` | HSN (Harmonized System) product codes |
| `lookup_sac_code` | SAC (Services Accounting Code) lookup |

## FQL (FinScreener Query Language)

FQL allows you to filter companies and GST registrations with powerful queries.

**IMPORTANT: Field names are CASE-SENSITIVE!**

### Operators
| Operator | Example |
|----------|---------|
| `==` | `City == 'Mumbai'` |
| `!=` | `State != 'Maharashtra'` |
| `>`, `>=`, `<`, `<=` | `paidUpCapital > 10000000` |
| `IN` | `NICCode IN [62011, 62012, 62013]` |
| `CONTAINS` | `company CONTAINS 'Tech'` |
| `STARTS_WITH` | `company STARTS_WITH 'Tata'` |
| `AND`, `OR` | `City == 'Mumbai' AND State == 'Maharashtra'` |

### Company Fields (Case-Sensitive!)
| Field | Type | Description |
|-------|------|-------------|
| `company` | String | Company name |
| `CIN` | String | Corporate Identification Number |
| `City` | String | City name (e.g., 'Mumbai', 'Bangalore') |
| `State` | String | State name (e.g., 'Maharashtra', 'Karnataka') |
| `paidUpCapital` | Number | Paid-up capital in INR |
| `authorisedCapital` | Number | Authorised capital in INR |
| `NICCode` | Number | NIC classification code (use with IN for multiple) |
| `mainDivision` | String | NIC main division code |
| `llpStatus` | String | Status: 'Active', 'Dormant', 'Struck Off', 'Under Liquidation' |
| `Listed` | String | Whether listed: 'Listed', 'Unlisted' |
| `companyType` | String | 'Private', 'Public', 'LLP', etc. |
| `dateOfIncorporation` | Date | Format: 'YYYY-MM-DD' |
| `pincode` | String | 6-digit pincode |
| `ROCCode` | String | Registrar of Companies code |

### GST Fields (Case-Sensitive!)
| Field | Type | Description |
|-------|------|-------------|
| `state` | String | **lowercase!** State name |
| `Status` | String | 'Active', 'Cancelled', 'Suspended' |
| `saccd` | String | SAC code for services |
| `hsncd` | String | HSN code for goods |
| `ConstitutionBusiness` | String | Business constitution type |
| `BusinessActivities` | String | Nature of business |
| `TradeName` | String | Trade name |
| `LegalName` | String | Legal name |
| `GSTIN` | String | 15-character GST number |
| `TaxpayerType` | String | Type of taxpayer |
| `DateOfRegistration` | Date | Registration date |

### Example Queries

```fql
# Mumbai IT companies with paid-up capital > 1 crore
City == 'Mumbai' AND NICCode IN [62011, 62012] AND paidUpCapital > 10000000

# Active software companies in Karnataka
State == 'Karnataka' AND llpStatus == 'Active' AND NICCode IN [62011, 62012, 62013]

# Listed companies in Maharashtra
State == 'Maharashtra' AND Listed == 'Listed'

# Companies incorporated after 2023
dateOfIncorporation > '2023-01-01' AND llpStatus == 'Active'

# Manufacturing companies in Gujarat
State == 'Gujarat' AND mainDivision == 'C'

# GST: Active registrations in Gujarat (note lowercase 'state')
state == 'Gujarat' AND Status == 'Active'

# GST: Software services
saccd IN ['998314', '998315'] AND Status == 'Active'
```

### Workflow: Industry Search

For fast industry-based search:
1. Use `lookup_nic_code(search="software")` to get NIC codes
2. Use `run_screener(query="NICCode IN [62011, 62012] AND City == 'Mumbai'", type="company")`

## Rate Limits

- **Detail endpoints** (company/director/GST details): 100 requests/day
- **Search/Filter endpoints**: Higher limits based on subscription
- **Screener queries**: May take longer for complex queries (timeout: 240s)

## API Endpoints Used

All tools use the Developer API (`/api/` prefix):

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/api-key/login` | Exchange API key for JWT token |
| `GET /api/company/company-filter` | Search/filter companies |
| `GET /api/company/director-filter` | Search/filter directors |
| `GET /api/gst/gst-filter` | Search/filter GST records |
| `GET /api/company/details` | Get company details (rate limited) |
| `GET /api/company/director-details` | Get director details (rate limited) |
| `GET /api/gst/details` | Get GST details (rate limited) |
| `GET/POST/DELETE /api/watchlist` | Watchlist CRUD operations |
| `POST /api/screener/search` | Execute FQL queries |
| `GET/POST/PUT/DELETE /api/screener/screeners` | Screener CRUD operations |
| `GET/POST /api/orders` | Order management |
| `GET /api/orders/{id}` | Get order details with contact data |
| `GET /api/orders/{id}/export` | Export order as JSON/CSV |
| `GET /api/crm/orders` | List orders for CRM integration |
| `GET /api/crm/orders/{id}/leads` | Get order as Zoho-ready leads |
| `POST /api/crm/newlead` | Get entity as Zoho lead format |
| `GET /api/reference/nic` | NIC code lookup |
| `GET /api/reference/hsn` | HSN code lookup |
| `GET /api/reference/sac` | SAC code lookup |
| `GET /api/users/me` | Get user profile and credits |

## Development

```bash
# Run server directly
python server.py

# Or as module
python -m mcp_server.server

# Test with MCP inspector
npx @modelcontextprotocol/inspector python server.py
```

## Troubleshooting

### "API key not set" error
Make sure `FINSCREENER_API_KEY` is set in your `.env` file or Claude Desktop config.

### "Invalid API key" error
Verify your API key starts with `fsk_` and is valid.

### Rate limit exceeded
Detail endpoints are limited to 100 requests/day. Use search/filter endpoints for bulk operations.

### Screener query timeout
Complex queries may take longer. The timeout is set to 240 seconds. Use indexed fields (`NICCode`, `City`, `State`) for faster queries.

### Wrong results from screener
Field names are **CASE-SENSITIVE**. Use `City` not `city`, `NICCode` not `nicCode`. Exception: GST uses lowercase `state`.

## License

Proprietary - Finscreener
