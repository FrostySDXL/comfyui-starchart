from aiohttp import web

routes = web.RouteTableDef()


def build_job(job_id):
    return {"id": job_id, "status": "completed"}


@routes.get("/ws")
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    return ws


@routes.get("/queue")
async def get_queue(request):
    return web.json_response({"queue_running": [], "queue_pending": []})


@routes.get("/api/jobs")
async def get_jobs(request):
    query = request.rel_url.query
    sort_by = query.get("sort_by", "created_at")
    sort_order = query.get("sort_order", "desc")
    limit = query.get("limit")
    offset = query.get("offset", 0)
    if sort_by not in {"created_at", "execution_duration"}:
        return web.json_response({"error": "bad sort"}, status=400)
    if sort_order not in {"asc", "desc"}:
        return web.json_response({"error": "bad order"}, status=400)
    return web.json_response(
        {
            "jobs": [],
            "pagination": {
                "offset": offset,
                "limit": limit,
                "total": 0,
                "has_more": False,
            },
        }
    )


@routes.get("/api/jobs/{job_id}")
async def get_job_by_id(request):
    """Get a single job by ID."""
    job_id = request.match_info.get("job_id", None)
    if not job_id:
        return web.json_response({"error": "job_id is required"}, status=400)
    job = build_job(job_id)
    return web.json_response(job)


@routes.post("/prompt")
async def post_prompt(request):
    payload = await request.json()
    prompt = payload["prompt"]
    client_id = payload.get("client_id")
    front = payload.get("front", False)
    if not prompt:
        return web.json_response({"error": "missing prompt", "node_errors": {}}, status=400)
    return web.json_response(
        {
            "prompt_id": payload.get("prompt_id", "generated-id"),
            "number": -1 if front else 1,
            "node_errors": {},
            "client_id": client_id,
        }
    )
