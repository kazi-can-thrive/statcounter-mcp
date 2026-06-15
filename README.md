# statcounter-mcp

An [MCP](https://modelcontextprotocol.io) server that wraps the
[StatCounter v3 HTTP API](https://api.statcounter.com/docs/v3) and exposes it
as tools any MCP client (Claude Code, Claude Desktop, etc.) can call.

## Authentication

StatCounter v3 authenticates with your **username** plus a separate
**API password**, using SHA-1 request signing:

- Each request includes `vn`, `u` (username), `t` (Unix timestamp), `f` (format).
- The `sha1` parameter is the SHA-1 of the full query string **with the API
  password appended**.
- The API password is used only to sign requests locally — it is **never
  transmitted or logged**.

> Requires a **paid StatCounter account** with the API password enabled in your
> account settings. The API password is *not* your login password.

## Setup

```bash
# 1. Clone and install (uv recommended)
git clone https://github.com/<you>/statcounter-mcp.git
cd statcounter-mcp
uv sync          # or: pip install -e .

# 2. Provide credentials
cp .env.example .env
# edit .env with your STATCOUNTER_USERNAME and STATCOUNTER_API_PASSWORD
```

The server reads credentials from the environment. Either export them or load
your `.env` before launching.

## Run

```bash
uv run server.py     # or: python server.py
```

The server speaks MCP over stdio.

## Register in Claude Code

```bash
claude mcp add statcounter \
  --env STATCOUNTER_USERNAME=your_username \
  --env STATCOUNTER_API_PASSWORD=your_api_password \
  -- uv run /absolute/path/to/statcounter-mcp/server.py
```

Or add it manually to your MCP config:

```json
{
  "mcpServers": {
    "statcounter": {
      "command": "uv",
      "args": ["run", "/absolute/path/to/statcounter-mcp/server.py"],
      "env": {
        "STATCOUNTER_USERNAME": "your_username",
        "STATCOUNTER_API_PASSWORD": "your_api_password"
      }
    }
  }
}
```

## Tools

| Tool | StatCounter endpoint | Purpose |
|------|----------------------|---------|
| `get_stats` | `/stats/` | Retrieve statistics for a project (summary, visitors, popular pages, etc.) |
| `user_details` | `/user_details/` | Account info and the list of projects on the account |
| `add_project` | `/add_project/` | Create a new project |
| `update_project` | `/update_project/` | Update an existing project's settings |

### `get_stats` parameters

- `project_id` *(required)* — the StatCounter project ID
- `stats_type` — `summary` (default), `visitor`, `popular`, `keyword_activity`, …
- `granularity` — `hourly`, `daily` (default), `weekly`, `monthly`
- `start_day` / `start_month` / `start_year` — optional start date, as separate components (StatCounter's `sd`/`sm`/`sy`)
- `end_day` / `end_month` / `end_year` — optional end date (`ed`/`em`/`ey`)

## Security notes

- Credentials live only in environment variables; nothing secret is committed
  (`.env` is git-ignored — see `.env.example`).
- The API password never leaves the process except as the SHA-1 signature.
- Requests are sent over HTTPS.

## License

MIT
