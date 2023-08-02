import re
from .mod import Mod, HTTPContent, ModTarget, Report


class CheckCommentsMod(Mod):
    async def check(self, thing: ModTarget):
        return 1 if isinstance(thing, HTTPContent) else 0

    async def crack(self, content: HTTPContent):
        comm = re.findall(r"<!--[\s\S]+?-->", content.text, flags=re.MULTILINE)
        if not comm:
            return []
        return [Report(f"在页面 {content.url} 找到以下注释：{comm}")]
