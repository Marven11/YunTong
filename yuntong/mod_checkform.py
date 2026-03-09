import re
from typing import List, cast
from urllib.parse import urlparse, urlunparse
from itertools import chain
from pathlib import Path

from bs4 import BeautifulSoup

from .mod import Mod, HTTPContent, ModTarget, Report, Page, SiteFolder, ModCrackResult


def _to_str(value: object) -> str:
    """将bs4属性值转换为字符串。"""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


class CheckHTMLFormMod(Mod):
    def __init__(self):
        super().__init__()
        self.visited = set()

    async def check(self, thing: ModTarget) -> float:
        if not isinstance(thing, HTTPContent):
            return 0
        if thing.url in self.visited:
            return 0
        url = urlparse(thing.url)
        if (
            url.path == ""
            or url.path.endswith("/")
            or any(url.path.endswith(word) for word in ["html", "php", "htm"])
        ):
            return 1
        return 0

    async def crack(self, thing: ModTarget) -> List[ModCrackResult]:
        if not isinstance(thing, HTTPContent):
            return []
        content = thing
        self.visited.add(content.url)
        bs = BeautifulSoup(content.text, "html.parser")
        urlobj = urlparse(content.url)
        forms: List[ModCrackResult] = []
        for form in bs.select("form"):
            action_attr = form.attrs.get("action")
            action = _to_str(action_attr) if action_attr else None
            if not action:
                form_uri = urlobj.path
            elif action.startswith("/"):
                form_uri = action
            else:
                form_uri = urlobj.path.rpartition("/")[0] + "/" + action
            form_uri = re.sub(r"[^/]+/\.\./", "", form_uri)
            form_uri = re.sub(r"\./", "", form_uri)
            method_attr = form.attrs.get("method", "POST")
            form_method = _to_str(method_attr).upper()
            inputs_value = {}
            for element in form.select("input"):
                name_attr = element.attrs.get("name")
                if not name_attr:
                    continue
                name = _to_str(name_attr)
                value_attr = element.attrs.get("value", "")
                value = _to_str(value_attr)
                inputs_value[name] = value
            inputs = list(inputs_value.keys())
            forms.append(
                Page(
                    url=urlunparse(
                        (
                            urlobj[0],
                            urlobj[1],
                            form_uri,
                            urlobj[3],
                            urlobj[4],
                            urlobj[5],
                        )
                    ),
                    mightbe=[],
                    params=inputs if form_method == "GET" else None,
                    data=inputs if form_method != "GET" else None,
                )
            )
        return forms
