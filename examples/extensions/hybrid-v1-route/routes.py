"""Route registration for the minimal hybrid extension example."""

from aiohttp import web

from server import PromptServer


def register_routes() -> None:
    prompt_server = PromptServer.instance
    if getattr(prompt_server, "_hybrid_v1_route_registered", False):
        return

    prompt_server._hybrid_v1_route_registered = True
    routes = prompt_server.routes

    @routes.get("/hybrid-v1-route/ping")
    async def hybrid_v1_route_ping(_request):
        return web.json_response(
            {
                "extension": "hybrid-v1-route",
                "node": "HybridStringEcho",
                "message": "route ready",
            }
        )
