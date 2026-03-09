import asyncio
from typing import List

from yuntong.mod import ModTarget

from .mod import Mod, Page, Report, Site, SiteFolder, ModCrackResult
from .requester import Requester


class VisitSiteMod(Mod):
    def __init__(self):
        super().__init__()

    async def check(self, thing: ModTarget) -> float:
        return 1 if isinstance(thing, Site) else 0

    async def crack(self, thing: ModTarget) -> List[ModCrackResult]:
        if not isinstance(thing, Site):
            return []
        site = thing
        return [
            Page(
                url=site.url,
                mightbe=[],
            ),
            SiteFolder(url=site.url + "/"),
        ]
