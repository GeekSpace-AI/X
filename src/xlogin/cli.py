from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .config import Config, load_dotenv
from .errors import XLoginError
from .manager import AuthManager
from .storage import default_store


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="xlogin", description="Secure X (Twitter) OAuth 2.0 login")
    p.add_argument(
        "--insecure-file-store",
        action="store_true",
        help="if no OS keyring exists, store tokens in a 0600 file (unencrypted)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    login = sub.add_parser("login", help="authorize this tool with your X account")
    login.add_argument("--no-browser", action="store_true", help="print the URL, don't open it")
    login.add_argument(
        "--manual",
        action="store_true",
        help="headless mode: no local server; paste the redirect URL back",
    )
    login.add_argument("--timeout", type=float, default=180.0, help="seconds to wait for login")
    sub.add_parser("whoami", help="show the logged-in account (refreshes token if needed)")
    sub.add_parser("status", help="show token state without any network call")
    sub.add_parser("refresh", help="force a token refresh")
    sub.add_parser("logout", help="revoke the token at X and delete it locally")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        load_dotenv()
        manager = AuthManager(Config.from_env(), default_store(args.insecure_file_store))
        return _run(args, manager)
    except XLoginError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("aborted", file=sys.stderr)
        return 130


def _run(args: argparse.Namespace, manager: AuthManager) -> int:
    if args.cmd == "login":
        token = manager.login(
            open_browser=not args.no_browser, manual=args.manual, timeout=args.timeout
        )
        print(f"Logged in. scopes: {token.scope or '(none reported)'}")
        me = manager.whoami()
        print(f"Account: @{me.get('username')} ({me.get('name')}, id={me.get('id')})")
    elif args.cmd == "whoami":
        me = manager.whoami()
        print(f"@{me.get('username')} ({me.get('name')}, id={me.get('id')})")
    elif args.cmd == "status":
        token = manager.stored_token()
        if token is None:
            print("not logged in")
            return 1
        state = "expired" if token.is_expired(skew=0) else "valid"
        print(f"access token: {state}; refresh token: {'yes' if token.refresh_token else 'no'}")
        print(f"scopes: {token.scope}")
    elif args.cmd == "refresh":
        manager.force_refresh()
        print("Token refreshed.")
    elif args.cmd == "logout":
        ok = manager.logout()
        print("Logged out." + ("" if ok else " (remote revoke failed; revoke in X settings)"))
    return 0
