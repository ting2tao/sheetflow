import os
import json
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import APIRouter, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

router = APIRouter(prefix="/analytics", tags=["analytics"])

ANALYTICS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "storage", "analytics"
)
os.makedirs(ANALYTICS_DIR, exist_ok=True)

# Paths to exclude from tracking
EXCLUDED_PREFIXES = ("/api/analytics", "/api/health", "/download", "/favicon", "/robots.txt", "/sitemap")
EXCLUDED_EXTENSIONS = (".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2")

DATA_RETENTION_DAYS = 90


def _get_analytics_path(date_str: str) -> str:
    return os.path.join(ANALYTICS_DIR, f"{date_str}.json")


def _load_day(date_str: str) -> dict:
    path = _get_analytics_path(date_str)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "date": date_str,
        "pageviews": 0,
        "visitors": {},  # hashed_ip -> count
        "pages": {},
        "referrers": {},
        "agents": {"desktop": 0, "mobile": 0, "other": 0},
    }


def _save_day(date_str: str, data: dict):
    path = _get_analytics_path(date_str)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def _classify_agent(user_agent: str) -> str:
    ua = user_agent.lower()
    if any(k in ua for k in ("mobile", "android", "iphone", "ipad")):
        return "mobile"
    if any(k in ua for k in ("mozilla", "chrome", "safari", "firefox", "edge")):
        return "desktop"
    return "other"


def _cleanup_old_files():
    """Remove analytics files older than DATA_RETENTION_DAYS."""
    cutoff = datetime.now() - timedelta(days=DATA_RETENTION_DAYS)
    for filename in os.listdir(ANALYTICS_DIR):
        if not filename.endswith(".json"):
            continue
        try:
            file_date = datetime.strptime(filename.replace(".json", ""), "%Y-%m-%d")
            if file_date < cutoff:
                os.remove(os.path.join(ANALYTICS_DIR, filename))
        except ValueError:
            continue


def _normalize_path(path: str) -> str:
    """Normalize path for analytics - strip job IDs and dynamic segments."""
    if path.startswith("/api/job/") or path.startswith("/api/download/") or path.startswith("/api/sheets/"):
        parts = path.split("/")
        if len(parts) >= 3:
            return "/" + "/".join(parts[:3]) + "/{id}"
    return path


def _extract_referer_host(referer: str) -> str:
    """Extract host from referer URL."""
    if not referer:
        return "direct"
    try:
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        return parsed.hostname or "direct"
    except Exception:
        return "direct"


# --- Middleware ---

class AnalyticsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip excluded paths
        if any(path.startswith(p) for p in EXCLUDED_PREFIXES):
            return await call_next(request)
        if any(path.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
            return await call_next(request)

        response = await call_next(request)

        # Only track successful page/API requests
        if response.status_code >= 400:
            return response

        try:
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")

            data = _load_day(date_str)
            data["pageviews"] += 1

            # Unique visitor tracking
            ip = request.client.host if request.client else "unknown"
            hashed = _hash_ip(ip)
            data["visitors"][hashed] = data["visitors"].get(hashed, 0) + 1

            # Page tracking
            normalized = _normalize_path(path)
            data["pages"][normalized] = data["pages"].get(normalized, 0) + 1

            # Referrer tracking
            referer = request.headers.get("referer", "")
            host = _extract_referer_host(referer)
            data["referrers"][host] = data["referrers"].get(host, 0) + 1

            # User agent classification
            ua = request.headers.get("user-agent", "")
            agent_type = _classify_agent(ua)
            data["agents"][agent_type] = data["agents"].get(agent_type, 0) + 1

            _save_day(date_str, data)

            # Periodic cleanup (1 in 100 chance)
            if now.minute == 0 and now.second < 10:
                _cleanup_old_files()
        except Exception:
            pass  # Never break the request for analytics

        return response


# --- API Endpoints ---

@router.get("/stats")
async def get_stats():
    """Return aggregated stats for the last 30 days."""
    today = datetime.now()
    total_pageviews = 0
    all_visitors = set()
    pages_agg = defaultdict(int)
    referrers_agg = defaultdict(int)
    agents_agg = defaultdict(int)
    daily = []

    for i in range(30):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        data = _load_day(date_str)

        total_pageviews += data["pageviews"]
        all_visitors.update(data.get("visitors", {}).keys())

        for page, count in data.get("pages", {}).items():
            pages_agg[page] += count
        for ref, count in data.get("referrers", {}).items():
            referrers_agg[ref] += count
        for agent, count in data.get("agents", {}).items():
            agents_agg[agent] += count

        daily.append({
            "date": date_str,
            "pageviews": data["pageviews"],
            "visitors": len(data.get("visitors", {})),
        })

    daily.reverse()

    return {
        "period": "30d",
        "total_pageviews": total_pageviews,
        "unique_visitors": len(all_visitors),
        "top_pages": dict(sorted(pages_agg.items(), key=lambda x: -x[1])[:20]),
        "top_referrers": dict(sorted(referrers_agg.items(), key=lambda x: -x[1])[:20]),
        "agents": dict(agents_agg),
        "daily": daily,
    }


@router.get("/today")
async def get_today():
    """Return today's stats."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    data = _load_day(date_str)
    return {
        "date": date_str,
        "pageviews": data["pageviews"],
        "unique_visitors": len(data.get("visitors", {})),
        "pages": data.get("pages", {}),
        "referrers": data.get("referrers", {}),
        "agents": data.get("agents", {}),
    }
