import asyncio
from pathlib import Path
from urllib.parse import urlparse

from .mod import Mod, Report, Page, ModTarget, SiteFolder
from .requester import Requester

uris = [
    ".git",
    ".git/HEAD",
    ".git/index",
    ".git/config",
    ".git/description",
    "source",
    "source.php",
    "source.php.bak",
    ".idea/workspace.xml",
    ".source.php.bak",
    "source.php.swp",
    "README.MD",
    "README.md",
    "README",
    ".gitignore",
    ".svn",
    ".svn/wc.db",
    ".svn/entries",
    "user.php.bak",
    ".hg",
    ".DS_store",
    "WEB-INF/web.xml",
    "WEB-INF/src/",
    "WEB-INF/classes",
    "WEB-INF/lib",
    "WEB-INF/database.propertie",
    "CVS/Root",
    "CVS/Entries",
    ".bzr/",
    "%3f",
    "%3f~",
    ".%3f.swp",
    ".%3f.swo",
    ".%3f.swn",
    ".%3f.swm",
    ".%3f.swl",
    "_viminfo",
    ".viminfo",
    "%3f~",
    "%3f~1~",
    "%3f~2~",
    "%3f~3~",
    "%3f.save",
    "%3f.save1",
    "%3f.save2",
    "%3f.save3",
    "%3f.bak_Edietplus",
    "%3f.bak",
    "%3f.back",
    "phpinfo.php",
    "robots.txt",
    ".htaccess",
    ".bash_history",
    ".svn/",
    ".git/",
    ".index.php.swp",
    "index.php.swp",
    "index.php.bak",
    ".index.php~",
    "index.php.bak_Edietplus",
    "index.php.~",
    "index.php.~1~",
    "index.php",
    "index.php~",
    "index.php.rar",
    "index.php.zip",
    "index.php.7z",
    "index.php.tar.gz",
    "index.php.txt",
    "login.php",
    "register",
    "register.php",
    "test.php",
    "upload.php",
    "phpinfo.php",
    "t.php",
    "www.zip",
    "www.rar",
    "www.zip",
    "www.7z",
    "www.tar.gz",
    "www.tar",
    "web.zip",
    "web.rar",
    "web.zip",
    "web.7z",
    "web.tar.gz",
    "web.tar",
    "plus",
    "qq.txt",
    "log.txt",
    "wwwroot.rar",
    "web.rar",
    "dede",
    "admin",
    "edit",
    "Fckeditor",
    "ewebeditor",
    "bbs",
    "Editor",
    "manage",
    "shopadmin",
    "web_Fckeditor",
    "login",
    "flag",
    "f1ag",
    "fl4g",
    "f14g",
    "f1ag.php",
    "fl4g.php",
    "f14g.php",
    "webadmin",
    "admin/WebEditor",
    "admin/daili/webedit",
    "login/",
    "database/",
    "tmp/",
    "manager/",
    "manage/",
    "web/",
    "admin/",
    "shopadmin/",
    "wp-includes/",
    "edit/",
    "editor/",
    "user/",
    "users/",
    "admin/",
    "home/",
    "test/",
    "administrator/",
    "houtai/",
    "backdoor/",
    "flag/",
    "upload/",
    "uploads/",
    "download/",
    "downloads/",
    "manager/",
    "root.zip",
    "root.rar",
    "wwwroot.zip",
    "wwwroot.rar",
    "backup.zip",
    "backup.rar",
    ".svn/entries",
    ".git/config",
    ".ds_store",
    "flag.php",
    "fl4g.php",
    "f1ag.php",
    "f14g.php",
    "admin.php",
    "4dmin.php",
    "adm1n.php",
    "4dm1n.php",
    "admin1.php",
    "admin2.php",
    "adminlogin.php",
    "administrator.php",
    "login.php",
    "register.php",
    "upload.php",
    "home.php",
    "log.php",
    "logs.php",
    "config.php",
    "member.php",
    "user.php",
    "users.php",
    "robots.php",
    "info.php",
    "phpinfo.php",
    "page.php",
    "backdoor.php",
    "fm.php",
    "example.php",
    "mysql.bak",
    "a.sql",
    "b.sql",
    "db.sql",
    "bdb.sql",
    "ddb.sql",
    "users.sql",
    "mysql.sql",
    "dump.sql",
    "data.sql",
    "backup.sql",
    "backup.sql.gz",
    "backup.sql.bz2",
    "backup.zip",
    "rss.xml",
    "crossdomain.xml",
    "1.txt",
    "flag.txt",
    "/wp-config.php",
    "/configuration.php",
    "/sites/default/settings.php",
    "/config.php",
    "/config.inc.php",
    "/conf/_basic_config.php",
    "/config/site.php",
    "/system/config/default.php",
    "/framework/conf/config.php",
    "/mysite/_config.php",
    "/typo3conf/localconf.php",
    "/config/config_global.php",
    "/config/config_ucenter.php",
    "/lib",
    "/data/config.php",
    "/data/config.inc.php",
    "/includes/config.php",
    "/data/common.inc.php",
    "/caches/configs/database.php",
    "/caches/configs/system.php",
    "/include/config.inc.php",
    "/phpsso_server/caches/configs/database.php",
    "/phpsso_server/caches/configs/system.php",
    "404.php",
    "index.html",
    "user/",
    "users/",
    "admin/",
    "home/",
    "install/",
    "test/",
    "administrator/",
    "houtai/",
    "backdoor/",
    "flag/",
    "uploads/",
    "download/",
    "downloads/",
    "manager/",
    "phpmyadmin/",
    "phpMyAdmin/",
]

httpfiles_dirsearch = []

with open(
    Path(__file__).parent / "fuzz_dict" / "httpfiles_dirsearch_php.txt", "r"
) as f:
    httpfiles_dirsearch = f.readlines()
    httpfiles_dirsearch = [param.strip() for param in httpfiles_dirsearch]

uris = list(set(uris))
uris_site = list(set(uris + httpfiles_dirsearch))
sem = asyncio.Semaphore(5)


class SiteBurstMod(Mod):
    def __init__(self, requester: Requester):
        super().__init__()
        self.requester = requester
        self.visited = set()

    async def fetch_with_sem(self, url):
        async with sem:
            return await self.requester.request("GET", url)

    async def check(self, thing: ModTarget) -> float:
        return (
            1 if isinstance(thing, SiteFolder) and thing.url not in self.visited else 0
        )

    async def crack(self, site_folder: SiteFolder):
        uri_lists = uris_site if urlparse(site_folder.url).path == "/" else uris
        self._logger.info("开始爆破站点 %s, 使用的字典长度为%d", site_folder.url, len(uri_lists))

        self.visited.add(site_folder.url)
        index_resp = await self.requester.request("GET", site_folder.url)
        nonexist_resp = await self.requester.request(
            "GET", site_folder.url + "114514asdfkhawer.ahaha"
        )
        valid_uris = []
        for batch_i in range(0, len(uri_lists), 500):
            results = await asyncio.gather(
                *[
                    self.fetch_with_sem(site_folder.url + uri.removeprefix("/"))
                    for uri in uri_lists[batch_i : batch_i + 500]
                ]
            )
            valid_uris += [
                uri
                for uri, result in zip(uri_lists, results)
                if result.status_code == 200
                and result.text != index_resp.text
                and result.text != nonexist_resp.text
                and result.text != ""
            ]
            if batch_i + 500 < len(uri_lists):
                self._logger.info(
                    "爆破站点 %s 已经完成了%.2f%%",
                    site_folder.url,
                    (batch_i + 500) / len(uri_lists) * 100,
                )
            await asyncio.sleep(0)
        if not valid_uris:
            return []
        return [
            Report(f"爆破站点目录 {site_folder.url} 完毕，其中存在以下文件泄露：{valid_uris}"),
        ] + [
            Page(url=site_folder.url + uri.removeprefix("/"), mightbe=[])
            for uri in valid_uris
        ]
