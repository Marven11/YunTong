from .mod import Mod, Page, ModTarget, HTTPContent
from .requester import Requester


class ScrapeContentMod(Mod):
    def __init__(self, requeser: Requester):
        super().__init__()
        self.requeser = requeser
        self.visited = set()

    async def check(self, thing: ModTarget):
        return 1 if isinstance(thing, Page) and thing.url not in self.visited else 0

    async def crack(self, page: Page):
        resp = await self.requeser.request(
            "GET", page.url, params=page.withparam, headers=page.withheaders
        )
        self.visited.add(page.url)
        if resp.status_code == 404:
            return []
        content = HTTPContent(
            frompage=page,
            url=page.url,
            text=resp.text,
            code=resp.status_code,
            headers={k.title(): v for k, v in resp.headers.items()},
        )
        return [
            content,
        ]
