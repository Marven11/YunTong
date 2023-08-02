import asyncio

from yuntong.mod import ModTarget

from .mod import Mod, Report, Site
from .requester import Requester

uris = [
    "/robots.txt",
    "/.git/HEAD",
    "/.index.php.swp",
    "/index.phps",
    "/.DS_Store",
    "/tz.php",
    "/www.zip",
    "/db/db.mdb",
    "/install/",
]


class SiteInfoLeakMod(Mod):
    def __init__(self, requester: Requester):
        super().__init__()
        self.requester = requester

    async def check(self, thing: ModTarget) -> float:
        return 1 if isinstance(thing, Site) else 0

    async def crack(self, site: Site):
        index_resp = await self.requester.request("GET", site.url)
        unexist_resp = await self.requester.request(
            "GET", site.url + "/whatareyoudoing.nonexist"
        )

        results = await asyncio.gather(
            *[self.requester.request("GET", site.url + uri) for uri in uris]
        )
        valid_uris = [
            uri
            for uri, result in zip(uris, results)
            if result.status_code == 200
            and result.text != index_resp.text
            and result.text != unexist_resp.text
        ]
        if not valid_uris:
            return []
        valid_uris = "\n".join(valid_uris)
        report = Report(f"在站点 {site.url} 中存在以下文件泄露：{valid_uris}")
        return [
            report,
        ]
