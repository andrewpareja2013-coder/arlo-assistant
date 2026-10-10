# =============================================================
# WEBSITE_TOOL.PY
# Opens a known website in the default browser. If a website isn't
# known, asks the user for its URL and saves it permanently into
# config.py's KNOWN_WEBSITES.
# =============================================================

import os
import webbrowser
import config
from tools.registry import register

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.py")


def _save_website_to_config(site_name, url):
    """Inserts a new entry into config.py's KNOWN_WEBSITES dictionary.
    Returns False if it couldn't be saved (the site still works for this session)."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_line = f'    {site_name!r}: {url!r},\n'

        in_known_websites = False
        insert_index = None

        for i, line in enumerate(lines):
            if line.strip().startswith("KNOWN_WEBSITES = {"):
                in_known_websites = True
                continue
            if in_known_websites and line.strip() == "}":
                insert_index = i
                break

        if insert_index is None:
            return False

        lines.insert(insert_index, new_line)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except Exception:
        return False


def open_website(site_name):
    site_name = site_name.lower().strip()
    if site_name in config.KNOWN_WEBSITES:
        url = config.KNOWN_WEBSITES[site_name]
        try:
            opened = webbrowser.open(url)
        except Exception:
            opened = False
        if not opened:
            return f"I couldn't open a browser for {site_name}, sir."
        return f"Opening {site_name}, sir."
    else:
        return f"NEEDS_WEBSITE_URL:{site_name}"


def add_and_open_website(site_name, url):
    url = str(url).strip().strip('"').strip("'")
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    config.KNOWN_WEBSITES[site_name] = url
    _save_website_to_config(site_name, url)
    return open_website(site_name)


register(
    name="open_website",
    description="Open a known website in the web browser, such as Spotify.",
    parameters={
        "type": "object",
        "properties": {"site_name": {"type": "string", "description": "Name of the website, e.g. 'spotify'."}},
        "required": ["site_name"],
    },
    function=open_website,
)

register(
    name="add_and_open_website",
    description="Internal use only.",
    parameters={
        "type": "object",
        "properties": {"site_name": {"type": "string"}, "url": {"type": "string"}},
        "required": ["site_name", "url"],
    },
    function=add_and_open_website,
)