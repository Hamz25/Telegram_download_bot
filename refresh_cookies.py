#!/usr/bin/env python3
"""
refresh_cookies.py

Standalone script to re-export cookies from a browser into a Netscape-format
cookies.txt file. Run this manually whenever a yt-dlp fallback tier fails
with an auth/cookie error, or stick it in a cron job.

Usage:
    python3 refresh_cookies.py --browser firefox --domain instagram.com --output /path/to/cookies.txt
    python3 refresh_cookies.py -b chrome -d tiktok.com -o /home/noops/cookies/tiktok_cookies.txt
    python3 refresh_cookies.py -b firefox:Profile1 -d instagram.com -o ./cookies.txt

Requires:
    pip install browser_cookie3 --break-system-packages
"""

import argparse
import http.cookiejar
import sys
from pathlib import Path

import browser_cookie3

BROWSER_FUNCS = {
    "chrome": browser_cookie3.chrome,
    "firefox": browser_cookie3.firefox,
    "edge": browser_cookie3.edge,
    "brave": browser_cookie3.brave,
    "opera": browser_cookie3.opera,
    "vivaldi": browser_cookie3.vivaldi,
    "safari": browser_cookie3.safari,
}


def get_cookie_jar(browser_spec: str, domain: str):
    """
    browser_spec can be 'firefox' or 'firefox:ProfileName' / 'chrome:Profile 1'
    """
    if ":" in browser_spec:
        browser_name, profile = browser_spec.split(":", 1)
    else:
        browser_name, profile = browser_spec, None

    browser_name = browser_name.lower()
    if browser_name not in BROWSER_FUNCS:
        sys.exit(f"[error] unsupported browser '{browser_name}'. choose from: {', '.join(BROWSER_FUNCS)}")

    func = BROWSER_FUNCS[browser_name]

    try:
        if profile:
            return func(domain_name=domain, profile=profile)
        return func(domain_name=domain)
    except Exception as e:
        sys.exit(f"[error] failed to read cookies from {browser_name}: {e}")


def save_netscape_cookies(cookiejar, output_path: str):
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    mozilla_cj = http.cookiejar.MozillaCookieJar(str(out))
    for cookie in cookiejar:
        mozilla_cj.set_cookie(cookie)

    mozilla_cj.save(ignore_discard=True, ignore_expires=True)
    return out, sum(1 for _ in cookiejar)


def main():
    parser = argparse.ArgumentParser(description="Refresh a cookies.txt file from a local browser.")
    parser.add_argument("-b", "--browser", required=True,
                         help="Browser to pull from: chrome, firefox, edge, brave, opera, vivaldi, safari. "
                              "Optionally with profile, e.g. firefox:default-release")
    parser.add_argument("-d", "--domain", required=True,
                         help="Domain to filter cookies for, e.g. instagram.com or tiktok.com")
    parser.add_argument("-o", "--output", required=True,
                         help="Path to write the cookies.txt file to")

    args = parser.parse_args()

    print(f"[*] reading cookies for '{args.domain}' from '{args.browser}'...")
    cj = get_cookie_jar(args.browser, args.domain)

    out_path, count = save_netscape_cookies(cj, args.output)
    print(f"[+] saved {count} cookie(s) to {out_path.resolve()}")


if __name__ == "__main__":
    main()
