import re
from typing import List
from urllib.parse import urlparse, urlunparse
from itertools import chain
from pathlib import Path

from bs4 import BeautifulSoup

from .mod import Mod, HTTPContent, ModTarget, Report, Page, SiteFolder


class CheckHTMLFormMod(Mod):
    def __init__(self):
        super().__init__()
        self.visited = set()

    async def check(self, thing: ModTarget):
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

    async def crack(self, content: HTTPContent):
        self.visited.add(content.url)
        bs = BeautifulSoup(content.text, "html.parser")
        urlobj = urlparse(content.url)
        forms: List[Page] = []
        for form in bs.select("form"):
            action = form.attrs.get("action")
            if not action:
                form_uri = urlobj.path
            elif action.startswith("/"):
                form_uri = action
            else:
                form_uri = urlobj.path.rpartition("/")[0] + "/" + action
            form_uri = re.sub(r"[^/]+/\.\./", "", form_uri)
            form_uri = re.sub(r"\./", "", form_uri)
            form_method = form.attrs.get("method", "POST").upper()
            inputs_value = {
                element.attrs["name"]: element.attrs.get("value", "")
                for element in form.select("input")
                if element.attrs.get("name")
            }
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
                    params = inputs if form_method == "GET" else None,
                    data = inputs if form_method != "GET" else None,
                )
            )
        return forms