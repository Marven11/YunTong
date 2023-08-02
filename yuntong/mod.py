from typing import List, Literal, Union, Dict
from logging import getLogger

from dataclasses import dataclass
from reprlib import Repr

reprobj = Repr()
reprobj.maxstring = 40


class Person:
    name: str
    age: int
    city: str


@dataclass
class Site:
    url: str


@dataclass
class SiteFolder:
    url: str


@dataclass
class Page:
    url: str
    mightbe: List[Literal["ssti", "sql", "lfi"]]
    params: Union[None, List[str]] = None
    data: Union[None, List[str]] = None

    withparam: Union[None, Dict[str, str]] = None
    withheaders: Union[None, Dict[str, str]] = None

    def __repr__(self) -> str:
        return f"Page(url={self.url}, params={self.params}, data={self.data}, ...)"


@dataclass
class HTTPContent:
    frompage: Page
    url: str
    code: int
    text: str
    headers: Dict[str, str]

    def __repr__(self) -> str:
        return f"HTTPContent(url={reprobj.repr(self.url)}, code={self.code}, text={reprobj.repr(self.text)}, ...)"


@dataclass
class VulunableParam:
    frompage: Page
    httpmethod: Literal["GET", "POST"]
    param: str



ModTarget = Union[Site, Page, HTTPContent]


@dataclass
class Report:
    msg: str


ModCrackResult = Union[ModTarget, Report]


class Mod:
    def __init__(self):
        self._logger = getLogger(self.__class__.__name__)

    async def check(self, thing: ModTarget) -> float:
        raise NotImplementedError()

    async def crack(self, thing: ModTarget) -> List[ModCrackResult]:
        raise NotImplementedError()
