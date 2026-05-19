"""Minimal idempotent route registration example."""

from aiohttp import web

from server import PromptServer


def register_routes() -> None:
    prompt_server = PromptServer.instance
    if getattr(prompt_server, "_minimal_route_registration_ready", False):
        return

    prompt_server._minimal_route_registration_ready = True
    routes = prompt_server.routes

    @routes.get("/minimal-route-registration/ping")
    async def minimal_route_registration_ping(_request):
        return web.json_response(
            {
                "extension": "minimal-route-registration",
                "message": "route ready",
            }
        )
