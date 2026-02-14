# TORQ Console API Documentation

## Crypto Price Endpoint

### Endpoint: `GET /api/crypto-price`

Returns current Bitcoin (BTC) price in USD with 24-hour change data.

### Request

No request body required. Simply make a GET request to the endpoint.

### Response

```json
{
  "success": true,
  "bitcoin": {
    "price_usd": 68850,
    "currency": "USD",
    "change_24h_percent": 3.42,
    "symbol": "BTC"
  },
  "last_updated": "Unknown",
  "timestamp": "2026-02-13T21:43:32.583980"
}
```

### Response Fields

- `success` (boolean) - Whether the request succeeded
- `bitcoin.price_usd` (number) - Current BTC price in USD
- `bitcoin.currency` (string) - Currency code (USD)
- `bitcoin.change_24h_percent` (number) - 24-hour price change percentage
- `bitcoin.symbol` (string) - BTC symbol
- `last_updated` (string) - When price was last updated (from API)
- `timestamp` (string) - ISO format timestamp of response

### Error Response

```json
{
  "success": false,
  "error": "Request timeout",
  "details": "API took too long to respond",
  "timestamp": "2026-02-13T21:43:32.583980"
}
```

### Example Usage

**cURL:**
```bash
curl http://127.0.0.1:8088/api/crypto-price
```

**JavaScript/Fetch:**
```javascript
const response = await fetch('http://127.0.0.1:8088/api/crypto-price');
const data = await response.json();
if (data.success) {
    console.log(`BTC Price: $${data.bitcoin.price_usd}`);
}
```

**Python:**
```python
import requests

response = requests.get('http://127.0.0.1:8088/api/crypto-price')
data = response.json()
if data['success']:
    print(f"BTC Price: ${data['bitcoin']['price_usd']}")
```

### Data Source

Data is fetched from CoinGecko API (https://api.coingecko.com/api/v3)

### Rate Limits

CoinGecko free tier has rate limits. For production use, consider:
1. Caching responses for 1-2 minutes
2. Using API key for higher rate limits
3. Implementing client-side rate limiting

---

## Chat Endpoint (BTC Price Query)

### Endpoint: `POST /api/chat`

You can query BTC price through the chat endpoint using natural language.

### Request

```json
{
  "message": "what is current btc price",
  "tab_id": "test"
}
```

### Response

```json
{
  "success": true,
  "response": "Current Bitcoin (BTC) price is $68,850.00 USD. 24h change: +3.42%.",
  "agent": "TORQ Console Enhanced AI",
  "timestamp": "2026-02-13T21:43:32.583980",
  "enhanced_mode": true
}
```

### Supported Query Patterns

The following natural language patterns will trigger BTC price lookup:
- "btc price"
- "bitcoin price"
- "price of btc"
- "price of bitcoin"
- "current btc"
- "current bitcoin"

### Example Usage

**cURL:**
```bash
curl -X POST http://127.0.0.1:8088/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what is current btc price", "tab_id": "test"}'
```

**JavaScript/Fetch:**
```javascript
const response = await fetch('http://127.0.0.1:8088/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: 'what is current btc price',
        tab_id: 'test'
    })
});
const data = await response.json();
console.log(data.response);
```

---

## Other Endpoints

### Health Check
`GET /api/health` - Returns system health status

### Chat Tabs
- `GET /api/chat/tabs` - List all chat tabs
- `POST /api/chat/tabs` - Create new chat tab
- `POST /api/chat/tabs/{tab_id}/switch` - Switch to specific tab
- `DELETE /api/chat/tabs/{tab_id}` - Close a tab
- `GET /api/chat/tabs/{tab_id}/messages` - Get messages from tab
- `POST /api/chat/tabs/{tab_id}/messages` - Send message to tab

### MCP Servers
- `GET /api/mcp/servers` - List connected MCP servers
- `POST /api/mcp/connect` - Connect to MCP server
- `GET /api/mcp/tools` - List available MCP tools
- `POST /api/mcp/call` - Call MCP tool

### Command Palette
- `GET /api/command-palette/commands` - Get all commands
- `POST /api/command-palette/search` - Search commands
- `POST /api/command-palette/execute` - Execute command

### Files & Code
- `GET /api/files` - List files in directory
- `GET /api/files/content` - Get file content
- `POST /api/files/save` - Save file content
- `GET /api/diff` - Get visual diff
- `POST /api/edit` - Perform AI-assisted edit
- `POST /api/inline-edit` - Handle inline editing

### Git
- `GET /api/git/status` - Get git status
- `POST /api/git/commit` - Commit changes
- `POST /api/git/reset` - Reset git changes

---

*Last Updated: 2026-02-13*
*TORQ Console v0.80.0*
