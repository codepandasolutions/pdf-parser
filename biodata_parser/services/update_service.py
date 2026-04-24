from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from biodata_parser.constants import APP_VERSION, GITHUB_RELEASES_API_URL, GITHUB_REPO


def check_for_updates() -> dict:
    if not GITHUB_REPO:
        return {
            "update_available": False,
            "latest_version": None,
            "download_url": None,
            "message": "GitHub repository is not configured yet.",
        }

    try:
        with urlopen(GITHUB_RELEASES_API_URL.format(repo=GITHUB_REPO), timeout=10) as response:
            payload = json.load(response)
    except (HTTPError, URLError) as exc:
        return {
            "update_available": False,
            "latest_version": None,
            "download_url": None,
            "message": f"Unable to check for updates: {exc}",
        }

    latest_version = str(payload.get("tag_name", "")).lstrip("v") or None
    assets = payload.get("assets") or []
    download_url = assets[0]["browser_download_url"] if assets else payload.get("html_url")
    return {
        "update_available": latest_version is not None and latest_version != APP_VERSION,
        "latest_version": latest_version,
        "download_url": download_url,
        "message": None,
    }
