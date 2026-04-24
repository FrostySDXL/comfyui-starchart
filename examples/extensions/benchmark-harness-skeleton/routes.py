"""Custom routes for the benchmark harness example."""

from aiohttp import web

from server import PromptServer


def register_routes(collector) -> None:
    prompt_server = PromptServer.instance
    if getattr(prompt_server, "_benchmark_harness_routes_registered", False):
        return

    prompt_server._benchmark_harness_routes_registered = True
    routes = prompt_server.routes

    @routes.get("/benchmark-harness/stats")
    async def benchmark_harness_stats(request):
        del request
        return web.json_response(collector.snapshot())
