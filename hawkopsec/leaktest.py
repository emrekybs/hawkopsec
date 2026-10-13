#!/usr/bin/env python3
"""
hawkopsec-leaktest — the GUI's leak test in the terminal (no Qt needed).

    hawkopsec-leaktest            # leak tests: IP, DNS, IPv6, WebRTC/STUN, kill-switch …
    hawkopsec-leaktest --all      # + dark-web pre-flight checklist
    hawkopsec-leaktest --json     # machine-readable output
    hawkopsec-leaktest --lang tr  # Turkish output (default: the GUI's language)

Exit code: 0 = no failures, 1 = at least one FAIL, 2 = interrupted.
"""
import argparse
import json
import sys

from . import audit, i18n
from .i18n import tr


class C:
    on = True

    @classmethod
    def w(cls, code, s):
        return f"\033[{code}m{s}\033[0m" if cls.on else s


STYLE = {"pass": "1;36", "warn": "1;33", "fail": "1;31", "info": "2", "skip": "2"}
TAG = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "info": "INFO", "skip": "SKIP"}
VERDICT = {"READY": ("Ready", "1;30;46"), "RISKY": ("Risky — review the warnings", "1;30;43"),
           "NOT READY": ("Not ready", "1;97;41")}


def _detail(c):
    try:
        return tr(c["detail"]).format(**{k: tr(v) for k, v in c.get("params", {}).items()})
    except (KeyError, IndexError):
        return c["detail"]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="hawkopsec-leaktest",
                                 description="DNS / IP / IPv6 / WebRTC leak test and dark-web pre-flight")
    ap.add_argument("--all", action="store_true", help="include the dark-web pre-flight checklist")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--no-color", action="store_true", help="plain output")
    ap.add_argument("--lang", choices=("en", "tr"), help="output language")
    a = ap.parse_args(argv)

    i18n.load_lang()
    if a.lang:
        i18n._lang = a.lang
    if a.no_color or a.json or not sys.stdout.isatty():
        C.on = False

    if not a.json:
        print(C.w("1;36", "\n  HawkOpsec — " + tr("Leak test")))
        print(C.w("2", "  " + tr("Takes 10–30 seconds; uses bash.ws for the DNS test.")) + "\n")
    try:
        res = audit.run_all()
    except KeyboardInterrupt:
        return 2

    checks = res["checks"] if a.all else [c for c in res["checks"] if c["group"] == "leak"]
    fails = sum(c["status"] == "fail" for c in checks)
    if a.json:
        out = {"verdict": res["verdict"], "ip": res.get("ip"),
               "checks": [{"id": c["id"], "group": c["group"], "title": c["title"],
                           "status": c["status"], "detail": _detail(c)} for c in checks]}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1 if fails else 0

    group = None
    for c in checks:
        if c["group"] != group:
            group = c["group"]
            head = tr("Leak tests") if group == "leak" else tr("Dark-web pre-flight")
            print(C.w("1", f"  {head}"))
            print(C.w("2", "  " + "─" * 66))
        tag = tr(TAG[c["status"]]).ljust(8)
        print(f"  {C.w(STYLE[c['status']], tag)} {C.w('1', tr(c['title']))}")
        print(C.w("2" if c["status"] in ("pass", "info", "skip") else STYLE[c["status"]],
                  f"           {_detail(c)}"))
    print()
    if a.all:
        txt, style = VERDICT.get(res["verdict"], (res["verdict"], "1"))
        print("  " + C.w(style, f"  {tr(txt)}  ") + "  " +
              tr("{p} of {t} checks passed · {f} failed · {w} warnings · {ts}").format(
                  p=res["passed"], t=res["total"], f=res["fails"], w=res["warns"], ts=res["ts"]))
    else:
        msg = (tr("No leaks found.") if not fails
               else tr("{n} leak(s) found.").format(n=fails))
        print("  " + C.w("1;97;41" if fails else "1;30;46", f"  {msg}  "))
    print()
    return 1 if fails else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
