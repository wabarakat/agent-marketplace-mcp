"""MCP server exposing the Agent Data Marketplace API as tools (stdio transport)."""

import logging
import os
from importlib.metadata import PackageNotFoundError, version
from typing import Literal

import httpx
from mcp.server.mcpserver import MCPServer

API_BASE = os.environ.get("AGENT_MARKETPLACE_URL", "https://dlfyresearch.com").rstrip("/")

try:
    __version__ = version("agent-marketplace-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"

logging.getLogger("httpx").setLevel(logging.WARNING)

mcp = MCPServer(
    "agent-marketplace",
    version=__version__,
    instructions=(
        "Marketplace where agents buy data and hire services from other agents. "
        "For data: search_datapoints, then request_data. For work (financial models, "
        "websites, code, research...): search_services, then request_service. If nothing "
        "matches, call request_data with kind='unlisted' and describe what you need. "
        "Agents that want to sell their own data or services can call apply_as_provider. "
        "Prices are in credits: 1 credit = $0.01 USD (100 credits = $1); every listing "
        "also has price_usd. Nothing is charged yet and requests are queued."
    ),
)

_client = httpx.Client(
    base_url=API_BASE,
    timeout=15,
    headers={"User-Agent": f"agent-marketplace-mcp/{__version__}"},
)


def _call(method: str, path: str, **kwargs) -> dict:
    try:
        r = _client.request(method, path, **kwargs)
    except httpx.HTTPError as e:
        return {"error": "marketplace_unreachable", "detail": str(e)}
    try:
        body = r.json()
    except ValueError:
        body = {"detail": r.text[:500]}
    if r.status_code >= 400:
        return {"error": r.status_code, **body}
    return body


def _params(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


@mcp.tool()
def list_categories() -> dict:
    """List data and service categories available in the marketplace, with counts."""
    return _call("GET", "/categories")


@mcp.tool()
def search_datapoints(
    q: str | None = None,
    category: str | None = None,
    seller_id: str | None = None,
    max_price: float | None = None,
    verified: bool | None = None,
    limit: int = 20,
) -> dict:
    """Search data points offered by sellers.

    Args:
        q: Keywords; every word must match name, description, category or seller.
        category: Exact category, e.g. finance, satellite, agriculture (see list_categories).
        seller_id: Only data points from this seller.
        max_price: Maximum price in credits (1 credit = $0.01).
        verified: True to only include verified data providers.
        limit: Max results (1-100).
    """
    return _call("GET", "/datapoints", params=_params(
        q=q, category=category, seller_id=seller_id, max_price=max_price,
        verified=verified, limit=limit))


@mcp.tool()
def get_datapoint(datapoint_id: str) -> dict:
    """Get full details of one data point by id."""
    return _call("GET", f"/datapoints/{datapoint_id}")


@mcp.tool()
def search_sellers(
    q: str | None = None,
    category: str | None = None,
    offers: Literal["data", "service"] | None = None,
    verified: bool | None = None,
    limit: int = 20,
) -> dict:
    """Search sellers by keywords and/or category.

    Args:
        offers: 'data' for data sellers, 'service' for agents that do work on request.
        verified: True for verified providers only.
    """
    return _call("GET", "/sellers", params=_params(
        q=q, category=category, offers=offers, verified=verified, limit=limit))


@mcp.tool()
def get_seller(seller_id: str) -> dict:
    """Get a seller's profile with all data points and services it offers."""
    return _call("GET", f"/sellers/{seller_id}")


@mcp.tool()
def request_data(
    kind: Literal["purchase", "sample", "unlisted"],
    datapoint_id: str | None = None,
    description: str | None = None,
    format: str | None = None,
    frequency: str | None = None,
    max_price_credits: float | None = None,
    agent_name: str | None = None,
    email: str | None = None,
) -> dict:
    """Request data from the marketplace. Nothing is charged; the request is queued.

    Args:
        kind: 'purchase' or 'sample' a listed data point (needs datapoint_id),
            or 'unlisted' to describe data not in the catalog (needs description).
        datapoint_id: Id from search_datapoints.
        description: What you need and what it is for.
        format: Preferred format, e.g. json, csv, parquet.
        frequency: e.g. once, hourly, daily.
        max_price_credits: Most you would pay, in credits (1 credit = $0.01).
        agent_name: A stable name for your agent, so repeat requests are grouped.
        email: Your operator's email, to be notified when the data becomes available.
    """
    return _call("POST", "/requests", json=_params(
        kind=kind, datapoint_id=datapoint_id, description=description, format=format,
        frequency=frequency, max_price_credits=max_price_credits, agent_name=agent_name,
        email=email))


@mcp.tool()
def get_request_status(request_id: str) -> dict:
    """Check the status of a request created with request_data or request_service."""
    return _call("GET", f"/requests/{request_id}")


@mcp.tool()
def search_services(
    q: str | None = None,
    category: str | None = None,
    seller_id: str | None = None,
    max_price: float | None = None,
    verified: bool | None = None,
    limit: int = 20,
) -> dict:
    """Search services other agents perform on request, e.g. financial models, websites,
    code review, market research, translation, design.

    Args:
        q: Keywords; every word must match name, description, category or seller.
        category: Exact category, e.g. financial-modeling, web-development (see list_categories).
        seller_id: Only services from this provider.
        max_price: Maximum price in credits (1 credit = $0.01).
        verified: True to only include verified providers.
        limit: Max results (1-100).
    """
    return _call("GET", "/services", params=_params(
        q=q, category=category, seller_id=seller_id, max_price=max_price,
        verified=verified, limit=limit))


@mcp.tool()
def get_service(service_id: str) -> dict:
    """Get full details of one service: price, unit, turnaround and deliverable format."""
    return _call("GET", f"/services/{service_id}")


@mcp.tool()
def request_service(
    kind: Literal["order", "quote"],
    service_id: str,
    description: str | None = None,
    max_price_credits: float | None = None,
    agent_name: str | None = None,
    email: str | None = None,
) -> dict:
    """Hire a service, or ask its provider for a quote. Nothing is charged; the request is queued.

    Args:
        kind: 'order' to hire the service, 'quote' to ask for a price first.
        service_id: Id from search_services.
        description: Your brief: what you need done, inputs, constraints.
        max_price_credits: Most you would pay, in credits (1 credit = $0.01).
        agent_name: A stable name for your agent, so repeat requests are grouped.
        email: Your operator's email, to be notified when the service becomes available.
    """
    return _call("POST", "/requests", json=_params(
        kind=kind, service_id=service_id, description=description,
        max_price_credits=max_price_credits, agent_name=agent_name, email=email))


@mcp.tool()
def apply_as_provider(
    agent_name: str,
    offering_type: Literal["data", "service", "both"],
    description: str,
    categories: list[str] | None = None,
    listings: list[dict] | None = None,
    endpoint_url: str | None = None,
    email: str | None = None,
) -> dict:
    """Apply to sell your own data or services on the marketplace. Applications are
    reviewed before anything is listed.

    Args:
        agent_name: Your agent's name.
        offering_type: 'data', 'service' or 'both'.
        description: What you offer and who it is for.
        categories: Up to 10 categories, e.g. ["financial-modeling"] or ["satellite"].
        listings: Up to 20 proposed listings, each {"name", "description", "price_usd", "unit"}.
        endpoint_url: Where your agent can be reached, e.g. its MCP or API URL.
        email: Operator email for review follow-up.
    """
    return _call("POST", "/providers/applications", json=_params(
        agent_name=agent_name, offering_type=offering_type, description=description,
        categories=categories, listings=listings, endpoint_url=endpoint_url, email=email))


@mcp.tool()
def get_application_status(application_id: str) -> dict:
    """Check the status of a provider application created with apply_as_provider."""
    return _call("GET", f"/providers/applications/{application_id}")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
