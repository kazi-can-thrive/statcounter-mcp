"""StatCounter MCP server.

Exposes the StatCounter v3 HTTP API (https://api.statcounter.com/docs/v3)
as MCP tools. Authenticates with a username + API password using the
documented SHA-1 request-signing scheme: the password is used locally to
sign each request and is NEVER transmitted or logged.

Required environment variables:
    STATCOUNTER_USERNAME       your StatCounter account username
    STATCOUNTER_API_PASSWORD   the API password set in your account

A paid StatCounter account with the API password enabled is required.
"""

import hashlib
import os
import time
from urllib.parse import urlencode

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = "https://api.statcounter.com"
API_VERSION = "3"

mcp = FastMCP("statcounter")


def _credentials() -> tuple[str, str]:
    """Read credentials from the environment, failing loudly if missing."""
    username = os.environ.get("STATCOUNTER_USERNAME")
    password = os.environ.get("STATCOUNTER_API_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "STATCOUNTER_USERNAME and STATCOUNTER_API_PASSWORD must be set "
            "in the environment."
        )
    return username, password


def _build_signed_url(path: str, params: dict[str, str]) -> str:
    """Build a signed StatCounter API URL.

    Per the v3 docs, the sha1 parameter is the SHA-1 of the full query
    string (vn, u, t, f, and any call-specific params) with the API
    password appended. The password itself is never part of the query.
    """
    username, password = _credentials()

    # Required params on every request. dict preserves insertion order,
    # so the query string we sign matches the one we send.
    query = {
        "vn": API_VERSION,
        "u": username,
        "t": str(int(time.time())),  # valid ~15 min server-side
        "f": "json",
        **params,
    }

    query_string = urlencode(query)

    # Per the v3 docs' worked example, the SHA-1 is computed over the query
    # string INCLUDING the leading "?", with the API password appended
    # directly (no separator).
    signature = hashlib.sha1(
        ("?" + query_string + password).encode("utf-8")
    ).hexdigest()
    return f"{BASE_URL}{path}?{query_string}&sha1={signature}"


async def _get(path: str, params: dict[str, str]) -> dict:
    """Issue a signed GET request and return the parsed JSON body."""
    url = _build_signed_url(path, params)
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_stats(
    project_id: str,
    stats_type: str = "summary",
    granularity: str = "daily",
    start_day: int | None = None,
    start_month: int | None = None,
    start_year: int | None = None,
    end_day: int | None = None,
    end_month: int | None = None,
    end_year: int | None = None,
) -> dict:
    """Retrieve statistics for a StatCounter project.

    Args:
        project_id: The StatCounter project ID (the `pi` value).
        stats_type: Stats resource to fetch, e.g. "summary", "visitor",
            "popular", "keyword_activity". Defaults to "summary".
        granularity: Time grouping, e.g. "hourly", "daily", "weekly",
            "monthly". Defaults to "daily".
        start_day / start_month / start_year: Optional start date, supplied
            as separate components (StatCounter's sd/sm/sy params).
        end_day / end_month / end_year: Optional end date (ed/em/ey).
    """
    params: dict[str, str] = {
        "s": stats_type,
        "pi": project_id,
        "g": granularity,
    }
    if start_day and start_month and start_year:
        params["sd"] = str(start_day)
        params["sm"] = str(start_month)
        params["sy"] = str(start_year)
    if end_day and end_month and end_year:
        params["ed"] = str(end_day)
        params["em"] = str(end_month)
        params["ey"] = str(end_year)
    return await _get("/stats/", params)


@mcp.tool()
async def user_details() -> dict:
    """Retrieve account details for the authenticated StatCounter user,
    including the list of projects on the account."""
    return await _get("/user_details/", {})


@mcp.tool()
async def add_project(
    website_title: str,
    website_url: str,
    timezone: str | None = None,
) -> dict:
    """Create a new StatCounter project.

    Args:
        website_title: Display name for the project.
        website_url: The website URL to track.
        timezone: Optional timezone string (e.g. "America/New_York").
    """
    params: dict[str, str] = {
        "wt": website_title,
        "wu": website_url,
    }
    if timezone:
        params["tz"] = timezone
    return await _get("/add_project/", params)


@mcp.tool()
async def update_project(
    project_id: str,
    website_title: str | None = None,
    website_url: str | None = None,
    timezone: str | None = None,
) -> dict:
    """Update settings for an existing StatCounter project.

    Args:
        project_id: The StatCounter project ID to update.
        website_title: Optional new display name.
        website_url: Optional new website URL.
        timezone: Optional new timezone string.
    """
    params: dict[str, str] = {"pi": project_id}
    if website_title:
        params["wt"] = website_title
    if website_url:
        params["wu"] = website_url
    if timezone:
        params["tz"] = timezone
    return await _get("/update_project/", params)


def main() -> None:
    """Entry point — run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
