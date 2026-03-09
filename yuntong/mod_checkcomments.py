import re
from typing import List
from .mod import Mod, HTTPContent, ModTarget, Report, ModCrackResult


class CheckCommentsMod(Mod):
    async def check(self, thing: ModTarget) -> float:
        return 1 if isinstance(thing, HTTPContent) else 0

    async def crack(self, thing: ModTarget) -> List[ModCrackResult]:
        if not isinstance(thing, HTTPContent):
            return []
        content = thing
        comm = re.findall(r"<!--[\s\S]+?-->", content.text, flags=re.MULTILINE)
        if not comm:
            return []
        return [Report(f"在页面 {content.url} 找到以下注释：{comm}")]
