import asyncio
import logging
import os
from contextlib import asynccontextmanager
from functools import partial

import tensorflow
from aiohttp.web import AppRunner, TCPSite, Application, get, post, json_response, Response
from generator.gpt2.gpt2_generator import GPT2Generator

from aidungeon import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_web_app(
        routes, host: str = settings.WEB_HOST, port: int = settings.WEB_PORT,
        shutdown_timeout=3, **kwargs,
):
    app = Application()
    app.add_routes(routes)
    runner = AppRunner(app)
    await runner.setup()
    site = TCPSite(runner, host=host, port=port, shutdown_timeout=shutdown_timeout, **kwargs)
    await site.start()
    try:
        logger.debug(f"Webserver started on {host}:{port}")
        yield
    finally:
        await runner.cleanup()


async def aidungeon_generate(generator, request):
    prompt = (await request.json())['prompt']
    return json_response(dict(text=generator.generate(prompt)))


async def run_aidungeon_server():
    generator = GPT2Generator(force_cpu=False)
    async with create_web_app([
        post(settings.AIDUNGEON_PATH, partial(aidungeon_generate, generator)),
        get('/ready', lambda request: Response()),
    ]):
        await asyncio.sleep(2 ** 32)


class GPUNotAvailable(Exception):
    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    if not tensorflow.test.is_gpu_available():
        raise GPUNotAvailable()
    asyncio.run(run_aidungeon_server())
