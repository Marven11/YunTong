import click
from . import core, mod
import asyncio


@click.command()
@click.option("--url", help="Your url")
def scansite(url):
    assert url is not None, "Please provide url with --url param!"
    asyncio.run(core.startat(mod.Site(url=url.removesuffix("/"))))


def main():
    scansite()
