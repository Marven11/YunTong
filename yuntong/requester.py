import logging
from typing import Dict, Literal
import httpx
import asyncio
import time

last_req_times = []
req_counts = 0
record_lock = asyncio.Lock()
sem = asyncio.Semaphore(12)
logger = logging.getLogger("Requester")
interval_lock = asyncio.Lock()
interval = 0.002

HTTPMethod = Literal["GET", "POST"]

def calculate_speed(last_req_times):
    assert len(last_req_times) >= 20
    sample_length = min(len(last_req_times) // 20 * 20, 100)
    return sample_length / (last_req_times[-1] - last_req_times[-sample_length])


class Requester:
    async def request_once(
        self, method: HTTPMethod, url: str, params: Dict[str, str] | None=None, data=None, headers=None
    ) -> httpx.Response:
        raise NotImplementedError()

    async def request(self, method, url, params=None, data=None, headers=None):
        for _ in range(4):
            await self.wait_interval()
            try:
                return await self.request_once(
                    method=method, url=url, params=params, data=data, headers=headers
                )
            except Exception:
                await asyncio.sleep(0)
        return await self.request_once(
            method=method, url=url, params=params, data=data, headers=headers
        )

    async def submit_to(self, url, method, params):
        if method == "GET":
            return await self.request(
                "GET",
                url,
                params=params,
            )
        elif method == "POST":
            return await self.request(
                "POST",
                url,
                data=params,
            )

    async def wait_interval(self):
        async with interval_lock:
            if not last_req_times:
                return
            duration = time.perf_counter() - last_req_times[-1]
            if duration < interval:
                await asyncio.sleep(interval - duration)

    async def record(self):
        global req_counts
        async with record_lock:
            last_req_times.append(time.perf_counter())
            req_counts += 1
            if req_counts % 100 == 0:
                speed = calculate_speed(last_req_times)
                logger.info(
                    "已经发出了%d次HTTP请求，速度为%.2freq/s",
                    req_counts,
                    speed
                )
            if req_counts > 1000:
                last_req_times.pop(0)


class StatelessRequester(Requester):
    async def request_once(self, method, url, params=None, data=None, headers=None):
        async with sem, httpx.AsyncClient(timeout=5) as client:
            resp = await client.request(
                method=method, url=url, params=params, data=data, headers=headers
            )
            await self.record()
            return resp


class StatefulRequester(Requester):
    def __init__(
        self,
    ):
        super().__init__()
        self.client = httpx.AsyncClient(timeout=5)

    async def request_once(self, method, url, params=None, data=None, headers=None):
        async with sem:
            resp = await self.client.request(
                method=method, url=url, params=params, data=data, headers=headers
            )
            await self.record()

            return resp
