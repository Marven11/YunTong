import asyncio
import logging
import reprlib
import time
from collections import deque, defaultdict

import yaml


from yuntong.mod_checkcomments import CheckCommentsMod
from yuntong.mod_checkheaders import CheckHeadersMod
from yuntong.mod_checkhtmllinks import CheckHTMLLinksMod
from yuntong.mod_checkform import CheckHTMLFormMod
from yuntong.mod_findparams import FindParamsMod
from yuntong.mod_findpostparams import FindPostParamsMod
from yuntong.mod_pageauthburst import PageAuthBurstMod
from yuntong.mod_phpevalfuzz import PHPEvalFuzzMod
from yuntong.mod_phpincludefuzz import PHPIncludeFuzzMod
from yuntong.mod_phpincludecrack import PHPIncludeCrackMod
from yuntong.mod_scrapecontent import ScrapeContentMod
from yuntong.mod_shellexecfuzz import ShellExecFuzzMod
from yuntong.mod_siteburst import SiteBurstMod
from yuntong.mod_siteinfoleak import SiteInfoLeakMod
from yuntong.mod_sqlfuzz import SQLFuzzMod
from yuntong.mod_sstifuzz import SSTIFuzzMod
from yuntong.mod_visitsite import VisitSiteMod
from yuntong.requester import StatefulRequester, StatelessRequester
from yuntong.mod import Mod, ModTarget, Report, Site

logging.basicConfig(level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
reprer = reprlib.Repr()
reprer.maxstring = 50
HANDLE_MOD_INTERVAL = 0.2

def default_requester():
    return StatefulRequester()


mods = [
    VisitSiteMod(),
    SiteInfoLeakMod(default_requester()),
    SiteBurstMod(StatefulRequester()),
    FindParamsMod(StatefulRequester()),
    FindPostParamsMod(StatefulRequester()),
    SQLFuzzMod(StatelessRequester()),
    SSTIFuzzMod(default_requester()),
    ScrapeContentMod(default_requester()),
    ShellExecFuzzMod(default_requester()),
    PageAuthBurstMod(StatelessRequester()),
    PHPEvalFuzzMod(default_requester()),
    PHPIncludeFuzzMod(default_requester()),
    PHPIncludeCrackMod(default_requester()),
    CheckCommentsMod(),
    CheckHeadersMod(),
    CheckHTMLLinksMod(),
    CheckHTMLFormMod(),
]

handle_mod_lock = asyncio.Lock()
handle_mod_last_run_time = time.perf_counter()

async def handle_mod(mod: Mod, target: ModTarget, queue, reports):
    global handle_mod_last_run_time
    if await mod.check(target) == 0:
        return
    async with handle_mod_lock:
        duration = time.perf_counter() - handle_mod_last_run_time
        if duration < HANDLE_MOD_INTERVAL:
            await asyncio.sleep(HANDLE_MOD_INTERVAL - duration)
    handle_mod_last_run_time = time.perf_counter()
    results = await mod.crack(target)
    for result in results:
        if isinstance(result, Report):
            logger.info(f"模块{mod.__class__.__name__}产生了新的报告：{reprer.repr(result.msg)}")
            reports[mod.__class__.__name__].append(result)
        else:
            logger.info(f"模块{mod.__class__.__name__}有了新的发现：{result}")
            queue.append(result)

async def handle_mods(target: ModTarget, queue, visited, reports):
    if any(target == other for other in visited):
        return
    visited.append(target)
    await asyncio.gather(
        *[handle_mod(mod, target, queue, reports) for mod in mods]
    )
    

async def startat(site: Site):
    queue = deque(
        [
            site,
        ]
    )
    visited = []
    reports_dict = defaultdict(list)
    coros = []

    while queue or coros:
        if queue:
            target = queue.popleft()
            logger.info("开始处理%s", repr(target))
            task = asyncio.create_task(handle_mods(target, queue, visited, reports_dict))
            coros.append(task)
        elif coros and any(coro.done() for coro in coros):
            done, coros = (
                [coro for coro in coros if coro.done()],
                [coro for coro in coros if not coro.done()],
            )
            for coro in done:
                await coro
        await asyncio.sleep(0)
    reports_dict = {
        name: [report.msg for report in reports]
        for name, reports in reports_dict.items()
    }
    logger.info("输出报告到reports.yaml...")
    with open("reports.yaml", "w") as f:
        yaml.dump(reports_dict, f, encoding="utf-8", allow_unicode=True, default_style="|")

