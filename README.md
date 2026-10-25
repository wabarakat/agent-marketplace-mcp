# agent-marketplace-mcp

<!-- mcp-name: io.github.wabarakat/agent-marketplace-mcp -->

MCP server for the [Agent Data Marketplace](https://dlfyresearch.com), a data
marketplace built for AI agents. Agents search data sellers (finance, satellite,
agriculture, weather, geo, research and more) and request datasets. No API key.

## Install

**Hosted (no install):** add this URL to any MCP client that supports remote servers:
```
https://dlfyresearch.com/mcp
```
Claude Code: `claude mcp add --transport http agent-marketplace https://dlfyresearch.com/mcp`

**Local (stdio)** via this package:

Claude Code:
```bash
claude mcp add agent-marketplace -- uvx agent-marketplace-mcp
```

Claude Desktop, Cursor and other clients (`mcpServers` JSON):
```json
{
  "agent-marketplace": {
    "command": "uvx",
    "args": ["agent-marketplace-mcp"]
  }
}
```

## Tools
| Tool | What it does |
|---|---|
| `list_categories` | Data categories with data point counts |
| `search_datapoints` | Search by keywords, category, seller, max price, verified providers |
| `get_datapoint` | One data point |
| `search_sellers` | Search sellers |
| `get_seller` | Seller profile and its data points |
| `request_data` | Purchase, sample, or describe data that isn't listed |
| `get_request_status` | Status of a request |

## Pricing
Prices are in credits: 1 credit = $0.01 USD. Each data point also shows `price_usd`.
Credits can't be purchased yet and nothing is charged: requests are queued and
you can check their status with `get_request_status`.

## Configuration
| Variable | Default |
|---|---|
| `AGENT_MARKETPLACE_URL` | `https://dlfyresearch.com` |

Requests from this server send `User-Agent: agent-marketplace-mcp/<version>`.

The HTTP API is also usable directly: see https://dlfyresearch.com/llms.txt and
https://dlfyresearch.com/openapi.json.

## License
MIT
