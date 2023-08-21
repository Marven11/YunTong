import click
from . import core, mod
import asyncio
from urllib.parse import urlparse


@click.command()
@click.option("--url", help="Your url")
def scansite(url: str):
    assert url is not None, "Please provide url with --url param!"
    host = urlparse(url).hostname
    assert host is not None
    site = mod.Site(url=url[:url.find(host) + len(host)])
    page = mod.Page(
        url = url,
        mightbe=[]
    )
    asyncio.run(core.startat(site, page))


def main():
    scansite()  # type: ignore
