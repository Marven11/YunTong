import re
from .mod import Mod, HTTPContent, ModTarget, Report

common_headers = set(
    [
        "WWW-Authenticate",
        "Authorization",
        "Proxy-Authenticate",
        "Proxy-Authorization",
        "Age",
        "Cache-Control",
        "Clear-Site-Data",
        "Expires",
        "Pragma",
        "Warning",
        "Accept-CH",
        "Accept-CH-Lifetime",
        "Critical-CH",
        "Sec-CH-Prefers-Reduced-Motion",
        "Sec-CH-UA",
        "Sec-CH-UA-Arch",
        "Sec-CH-UA-Bitness",
        "Sec-CH-UA-Full-Version",
        "Sec-CH-UA-Full-Version-List",
        "Sec-CH-UA-Mobile",
        "Sec-CH-UA-Model",
        "Sec-CH-UA-Platform",
        "Sec-CH-UA-Platform-Version",
        "Content-DPR",
        "Device-Memory",
        "DPR",
        "Viewport-Width",
        "Width",
        "Downlink",
        "ECT",
        "RTT",
        "Save-Data",
        "Last-Modified",
        "ETag",
        "If-Match",
        "If-None-Match",
        "If-Modified-Since",
        "If-Unmodified-Since",
        "Vary",
        "Connection",
        "Keep-Alive",
        "Accept",
        "Accept-Encoding",
        "Accept-Language",
        "Expect",
        "Max-Forwards",
        "Cookie",
        "Set-Cookie",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Credentials",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Methods",
        "Access-Control-Expose-Headers",
        "Access-Control-Max-Age",
        "Access-Control-Request-Headers",
        "Access-Control-Request-Method",
        "Origin",
        "Timing-Allow-Origin",
        "Content-Disposition",
        "Content-Length",
        "Content-Type",
        "Content-Encoding",
        "Content-Language",
        "Content-Location",
        "Forwarded",
        "X-Forwarded-For",
        "X-Forwarded-Host",
        "X-Forwarded-Proto",
        "Via",
        "Location",
        "Refresh",
        "From",
        "Host",
        "Referer",
        "Referrer-Policy",
        "User-Agent",
        "Allow",
        "Server",
        "Accept-Ranges",
        "Range",
        "If-Range",
        "Content-Range",
        "Cross-Origin-Embedder-Policy",
        "Cross-Origin-Opener-Policy",
        "Cross-Origin-Resource-Policy",
        "Content-Security-Policy",
        "CSP",
        "Content-Security-Policy-Report-Only",
        "Expect-CT",
        "Origin-Isolation",
        "Permissions-Policy",
        "Strict-Transport-Security",
        "HSTS",
        "Upgrade-Insecure-Requests",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-Permitted-Cross-Domain-Policies",
        "X-Powered-By",
        "X-XSS-Protection",
        "Sec-Fetch-Site",
        "Sec-Fetch-Mode",
        "Sec-Fetch-User",
        "Sec-Fetch-Dest",
        "Sec-Purpose",
        "Service-Worker-Navigation-Preload",
        "Last-Event-ID",
        "NEL",
        "Ping-From",
        "Ping-To",
        "Report-To",
        "Transfer-Encoding",
        "TE",
        "Trailer",
        "Sec-WebSocket-Key",
        "Sec-WebSocket-Extensions",
        "Sec-WebSocket-Accept",
        "Sec-WebSocket-Protocol",
        "Sec-WebSocket-Version",
        "Accept-Push-Policy",
        "Accept-Signature",
        "Alt-Svc",
        "Alt-Used",
        "Date",
        "Early-Data",
        "Large-Allocation",
        "Link",
        "Push-Policy",
        "Retry-After",
        "Signature",
        "Signed-Headers",
        "Server-Timing",
        "Service-Worker-Allowed",
        "SourceMap",
        "Upgrade",
        "X-DNS-Prefetch-Control",
        "X-Firefox-Spdy",
        "X-Pingback",
        "X-Requested-With",
        "X-Robots-Tag",
        "Etag"
    ]
)


class CheckHeadersMod(Mod):
    async def check(self, thing: ModTarget):
        return 1 if isinstance(thing, HTTPContent) else 0

    async def crack(self, content: HTTPContent):
        uncommon_headers = {
            k: v for k, v in content.headers.items() if k not in common_headers
        }
        reports = []
        if uncommon_headers:
            reports.append(
                Report(f"在页面 {content.url} 找到以下异常headers：{uncommon_headers}")
            )
        if "Set-Cookie" in content.headers:
            reports.append(
                Report(f"页面 {content.url} 设置了以下cookie: {content.headers['Set-Cookie']}")
            )
        if "Cookie" in content.headers:
            reports.append(
                Report(f"页面 {content.url} 有以下cookie: {content.headers['Cookie']}")
            )

        return reports
