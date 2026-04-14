import os
import time
from collections import defaultdict, deque
from logging import getLogger

from aiohttp import web

log = getLogger(__name__)

# Rate limiter dictionary: {ip_address: deque([timestamp1, timestamp2, ...])}
rate_limit_records = defaultdict(deque)
# Allow 2 requests per 10 seconds per IP for aggressive rate limiting
RATE_LIMIT_REQUESTS = 2
RATE_LIMIT_WINDOW = 10


@web.middleware
async def rate_limit_middleware(request, handler):
    ip = request.remote
    current_time = time.time()

    records = rate_limit_records[ip]

    # Remove timestamps that are outside the rate limit window
    while records and current_time - records[0] >= RATE_LIMIT_WINDOW:
        records.popleft()

    if len(records) >= RATE_LIMIT_REQUESTS:
        return web.Response(text="Too Many Requests", status=429)

    records.append(current_time)
    return await handler(request)


async def health_check(_request):
    return web.Response(text="OK", status=200)


async def start_health_server():
    app = web.Application(middlewares=[rate_limit_middleware])
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    log.info(f"Health check server started on port {port}")
