# Claude Code & API Documentation Review

## 📋 Review Summary

**Date**: 2025-01-15
**Requested By**: User
**Purpose**: Review Claude Code documentation and new API integrations

---

## 🔄 Claude Code SDK → Claude Agent SDK Migration

### Important Name Change

The **Claude Code SDK** has been renamed to **Claude Agent SDK** to reflect its broader capabilities beyond just coding tasks.

### Migration Required

If you're using the old SDK, you need to migrate:

#### **TypeScript/JavaScript Migration**
```bash
# 1. Uninstall old package
npm uninstall @anthropic-ai/claude-code

# 2. Install new package
npm install @anthropic-ai/claude-agent-sdk

# 3. Update imports in code
# Old: import { ... } from '@anthropic-ai/claude-code'
# New: import { ... } from '@anthropic-ai/claude-agent-sdk'
```

#### **Python Migration**
```bash
# 1. Uninstall old package
pip uninstall claude-code-sdk

# 2. Install new package
pip install claude-agent-sdk

# 3. Update imports in code
# Old: from claude_code_sdk import ...
# New: from claude_agent_sdk import ...
```

### Breaking Changes

⚠️ **Important API Changes**:

1. **System Prompt**: No longer default - must be explicitly provided
2. **Settings Sources**: No longer automatically loaded - must be configured
3. **Python Class Rename**: `ClaudeCodeOptions` → `ClaudeAgentOptions`

### Recommended Actions for TORQ Console

**Priority**: Medium (not currently using SDK, but good to know)

1. **No Immediate Action Required**: TORQ Console doesn't currently use the SDK
2. **Future Integration**: If we integrate Claude Agent SDK, use the new package name
3. **Documentation**: Update any references from "Claude Code SDK" to "Claude Agent SDK"

---

## 💰 CoinGecko API Integration

### Available Endpoints

CoinGecko provides comprehensive cryptocurrency market data through two API families:

#### **1. CoinGecko API Endpoints**

**Global Data**:
- `/global` - Global crypto market metrics (total market cap, volumes, etc.)

**Coin Information**:
- `/coins/{id}` - Detailed coin data (price, market cap, volume, description)
- `/coins/list` - List all supported coins
- `/coins/markets` - Market data for multiple coins

**Exchange Data**:
- `/exchanges/{id}` - Exchange details and trading pairs
- `/exchanges/list` - List of all exchanges

**NFT Information**:
- `/nfts/{id}` - NFT collection data
- `/nfts/list` - List of NFT collections

**Price & Market Data**:
- `/simple/price` - Quick price lookup for coins
- `/coins/{id}/market_chart` - Historical price data
- `/coins/{id}/tickers` - Real-time ticker data

#### **2. GeckoTerminal Endpoints (On-chain Data)**

**Network Data**:
- `/onchain/networks/{network}/pools` - Pool information for specific network
- `/onchain/networks/{network}/tokens/{token}` - Token details

**Trending & Discovery**:
- `/onchain/trending` - Trending pools
- `/onchain/new_pools` - Recently created pools

**Categories**:
- `/onchain/categories` - Cryptocurrency categories

### Authentication & Rate Limits

⚠️ **Not Specified in Endpoint Showcase**

The endpoint showcase doesn't detail:
- API key acquisition process
- Authentication headers required
- Rate limits per tier
- Pricing tiers

**Action Required**: Visit CoinGecko's main API documentation or developer portal for:
- API key registration
- Rate limit information
- Authentication requirements
- Usage quotas

### Integration Recommendations for TORQ Console

#### **Use Case 1: Crypto Market Research**

**Endpoint**: `/coins/{id}`
**Purpose**: Integrate cryptocurrency data into research topics
**Example**: "Research Bitcoin market trends" → fetch BTC data from CoinGecko

```python
# Potential integration
async def research_crypto_topic(coin_id: str):
    """Research cryptocurrency with market data."""
    # 1. Fetch coin data from CoinGecko API
    coin_data = await fetch_coingecko_data(f"/coins/{coin_id}")

    # 2. Perform web search for news/analysis
    search_results = await provider.search(f"{coin_id} cryptocurrency analysis")

    # 3. Combine market data + web research
    # 4. Export with Phase 5 export system
```

#### **Use Case 2: Market Intelligence Tool**

**Endpoints**: `/simple/price`, `/coins/markets`, `/global`
**Purpose**: Real-time market monitoring tool
**Features**:
- Track portfolio values
- Alert on price changes
- Export market reports (using Phase 5)

#### **Use Case 3: NFT Research Enhancement**

**Endpoint**: `/nfts/{id}`
**Purpose**: Add NFT market data to research capabilities
**Integration**: Add as search plugin (Phase 3 plugin system)

### Recommended Next Steps

1. **Get API Key**
   - Visit: https://www.coingecko.com/en/api
   - Register for free or pro tier
   - Store key in `.env` file: `COINGECKO_API_KEY=your_key_here`

2. **Create CoinGecko Integration Module**
   ```
   torq_console/
   └── integrations/
       └── coingecko/
           ├── __init__.py
           ├── client.py         # API client
           ├── endpoints.py      # Endpoint definitions
           └── models.py         # Data models
   ```

3. **Add to Search Plugins**
   - Create `CoinGeckoSearchPlugin` in Phase 3 plugin system
   - Enable cryptocurrency-specific searches
   - Integrate with export system (Phase 5)

4. **Environment Configuration**
   ```bash
   # Add to .env
   COINGECKO_API_KEY=your_api_key_here
   COINGECKO_API_TIER=free  # or pro, enterprise
   COINGECKO_RATE_LIMIT=50  # requests per minute (check your tier)
   ```

---

## 📚 Additional Resources

### Claude Agent SDK
- **Overview**: https://docs.claude.com/en/docs/claude-agent-sdk
- **TypeScript Reference**: https://docs.claude.com/en/docs/claude-agent-sdk/typescript
- **Python Reference**: https://docs.claude.com/en/docs/claude-agent-sdk/python
- **Custom Tools**: https://docs.claude.com/en/docs/claude-agent-sdk/custom-tools
- **MCP Integration**: https://docs.claude.com/en/docs/claude-agent-sdk/mcp

### CoinGecko API
- **Main API Docs**: https://www.coingecko.com/en/api/documentation
- **Endpoint Showcase**: https://docs.coingecko.com/docs/endpoint-showcase
- **API Key Registration**: https://www.coingecko.com/en/api
- **Rate Limits**: Check official docs for your tier
- **Support**: https://www.coingecko.com/en/api/support

---

## ✅ Action Items

### Immediate
- [x] Review Claude Code documentation ✅
- [x] Review CoinGecko API documentation ✅
- [x] Document findings ✅

### Short Term (Optional)
- [ ] Register for CoinGecko API key
- [ ] Test CoinGecko API endpoints
- [ ] Create CoinGecko integration module
- [ ] Add crypto search plugin to Phase 3

### Long Term (Future Enhancement)
- [ ] Integrate Claude Agent SDK if needed
- [ ] Build crypto market intelligence tool
- [ ] Add NFT research capabilities
- [ ] Create automated crypto reports with Phase 5 export

---

## 🎯 Impact on TORQ Console

### Current Phase 5 Implementation
✅ **No Changes Required**
- Phase 5 Export & Progress systems are independent
- All features working as designed
- 100% test pass rate maintained

### Future Enhancements
🚀 **Potential Improvements**
- Add cryptocurrency research capabilities
- Integrate real-time market data
- Export crypto market reports (already supported by Phase 5)
- Create specialized crypto research workflows

### Compatibility
✅ **Fully Compatible**
- CoinGecko API can be added as new search plugin
- Phase 3 plugin system designed for this
- Phase 5 export supports any data format
- No breaking changes required

---

## 📝 Summary

1. **Claude Code → Claude Agent SDK**: Renamed but not currently used in TORQ Console
2. **CoinGecko API**: Excellent opportunity for crypto market integration
3. **Phase 5 Status**: Complete and unaffected by these findings
4. **Recommendation**: Consider CoinGecko integration as future Phase 6 enhancement

---

*Review completed: 2025-01-15*
*TORQ Console - Phase 5 Complete*
