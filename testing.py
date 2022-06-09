import asyncio
import datetime
import time
from asyncio import get_event_loop, new_event_loop

import aiohttp


async def calc(i, session):
    async with session.get('http://127.0.0.1:8000') as resp:
        print(datetime.datetime.now(), i)

async def fetch_many(loop):
    async with aiohttp.ClientSession() as session:
        tasks = [loop.create_task(calc(i, session)) for i in range(100)]
        return await asyncio.gather(*tasks)


if __name__ == '__main__':
    loop = get_event_loop()
    loop.run_until_complete(fetch_many(loop))
