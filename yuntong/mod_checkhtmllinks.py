import re
from typing import List, Set
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup
from .mod import Mod, HTTPContent, ModTarget, Report, Page, SiteFolder, ModCrackResult


def _to_str(value: object) -> str:
    """将bs4属性值转换为字符串。"""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


class CheckHTMLLinksMod(Mod):
    def __init__(self):
        super().__init__()
        self.visited: Set[str] = set()
        self.visited_folders: Set[str] = set()
        self.visited_paths: Set[str] = set()

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
        paths: Set[str] = set()
        dirs: Set[str] = set()
        for elements, attrname in zip(
            [
                bs.select("a"),
                bs.select("link[rel='stylesheet']"),
                bs.select("script[src]"),
            ],
            ["href", "href", "src"],
        ):
            for element in elements:
                attr_value = element.attrs.get(attrname)
                if not attr_value:
                    continue
                path = _to_str(attr_value)
                if (
                    path.startswith("http")
                    or path.startswith("//")
                    or path.startswith("javascript:")
                ):
                    continue
                if not path.startswith("/"):
                    path = urlobj.path.removesuffix("/") + "/" + path
                path = re.sub(r"[^/]+/\.\./", "", path)
                path = re.sub(r"\./", "", path)
                paths.add(path)
        for result in re.finditer(
            r"(?<=location=['\"])([0-9A-Za-z-_/.]+)(?=['\"])", content.text
        ):
            path = result.group(1)
            if not path.startswith("/"):
                path = urlobj.path.removesuffix("/") + "/" + path
            path = re.sub(r"[^/]+/\.\./", "", path)
            path = re.sub(r"\./", "", path)
            paths.add(path)
        for path in list(paths):
            p = path
            while "/" in p:
                p = p.rpartition("/")[0]
                dirs.add(p + "/")
        dir_urls = [
            urlunparse(
                (
                    urlobj[0],
                    urlobj[1],
                    path,
                    urlobj[3],
                    urlobj[4],
                    urlobj[5],
                )
            )
            for path in dirs
        ]
        dir_urls = [
            dir_url for dir_url in dir_urls if dir_url not in self.visited_folders
        ]

        page_urls = [
            urlunparse(
                (
                    urlobj[0],
                    urlobj[1],
                    path,
                    urlobj[3],
                    urlobj[4],
                    urlobj[5],
                )
            )
            for path in paths
        ]
        page_urls = [url for url in page_urls if url not in self.visited_paths]
        for dir_url in dir_urls:
            self.visited_folders.add(dir_url)
        for url in page_urls:
            self.visited_paths.add(url)
        results: List[ModCrackResult] = []
        for url in page_urls + dir_urls:
            results.append(Page(url=url, mightbe=[]))
        for dir_url in dir_urls:
            results.append(SiteFolder(url=dir_url))
            results.append(Report(f"找到新的目录：{dir_url}"))
        return results
