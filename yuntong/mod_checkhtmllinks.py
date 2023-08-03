import re
from urllib.parse import urlparse, urlunparse
from itertools import chain
from bs4 import BeautifulSoup
from .mod import Mod, HTTPContent, ModTarget, Report, Page, SiteFolder


class CheckHTMLLinksMod(Mod):
    def __init__(self):
        super().__init__()
        self.visited = set()
        self.visited_folders = set()
        self.visited_paths = set()

    async def check(self, thing: ModTarget):
        if not isinstance(thing, HTTPContent):
            return 0
        if thing.url in self.visited:
            return 0
        url = urlparse(thing.url)
        if url.path == "" or url.path.endswith("/") or any(
            url.path.endswith(word) for word in ["html", "php", "htm"]
        ):
            return 1
        return 0

    async def crack(self, content: HTTPContent):
        self.visited.add(content.url)
        bs = BeautifulSoup(content.text, "html.parser")
        urlobj = urlparse(content.url)
        paths = set()
        dirs = set()
        for elements, attrname in zip(
            [
                bs.select("a"),
                bs.select("link[rel='stylesheet']"),
                bs.select("script[src]"),
            ],
            ["href", "href", "src"],
        ):
            for element in elements:
                if not element.attrs.get(attrname):
                    continue
                path = element.attrs.get(attrname)
                assert path is not None
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
        for result in re.finditer(r"(?<=location=['\"])[0-9A-Za-z-_/.]+(?=['\"])", content.text):
            print(result)
            assert isinstance(result, re.Match), type(result)
            path = result.group(0)
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

        paths = [
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
        paths = [path for path in paths if path not in self.visited_paths]
        for dir_url in dir_urls:
            self.visited_folders.add(dir_url)
        for path in paths:
            self.visited_paths.add(path)
        return (
            [
                Page(
                    url=path,
                    mightbe=[],
                )
                for path in paths + dir_urls
            ]
            + [SiteFolder(url=dir_url) for dir_url in dir_urls]
            + [Report("找到新的目录：{url}".format(url=dir_url)) for dir_url in dir_urls]
        )
