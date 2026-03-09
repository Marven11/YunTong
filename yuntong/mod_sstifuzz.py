import asyncio
from typing import List

from .mod import Mod, Page, Report, ModTarget, ModCrackResult
from .requester import Requester

payloads = [("{{114*514}}", "58596"), ("{%print(114*514)%}", "58596")]


class SSTIFuzzMod(Mod):
    def __init__(self, requester: Requester):
        super().__init__()
        self.requeser = requester

    async def check(self, thing: ModTarget) -> float:
        if not isinstance(thing, Page) or not thing.params:
            return 0
        return 2 if "ssti" in thing.mightbe else 1

    async def crack(self, thing: ModTarget) -> List[ModCrackResult]:
        if not isinstance(thing, Page) or not thing.params:
            return []
        page = thing
        # 告诉类型检查器page.params不为None
        assert page.params is not None
        reports: List[ModCrackResult] = []
        for param in page.params:
            result = await asyncio.gather(
                *[
                    self.requeser.request(
                        "GET",
                        page.url,
                        params={
                            k: payload if k == param else "asdf" for k in page.params
                        },
                    )
                    for payload, _ in payloads
                ]
            )
            for (_, payload_respond), resp in zip(payloads, result):
                if payload_respond in resp.text:
                    reports.append(
                        Report(msg=f"在页面 {page.url} 找到一个可以SSTI的参数{param}")
                    )
                    break
        return reports
