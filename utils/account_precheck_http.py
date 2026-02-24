"""
账号预检：HTTP 与登录细节。
"""

from __future__ import annotations

import http.cookiejar
import json as _json
import ssl
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

from utils.logger import get_logger

logger = get_logger(__name__)

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def _http_post_form(
    url: str,
    data: Dict[str, str],
    headers: Optional[Dict[str, str]] = None,
    timeout_s: int = 15,
) -> Tuple[int, str]:
    ctx = ssl._create_unverified_context()
    body = urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("content-type", "application/x-www-form-urlencoded")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout_s) as r:
            raw = r.read()
            return r.status, raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        raw = b""
        try:
            raw = e.read()
        except Exception:
            pass
        return e.code, raw.decode("utf-8", "ignore")


def _http_post_json(
    url: str,
    payload: Dict[str, Any],
    *,
    opener: Optional[urllib.request.OpenerDirector] = None,
    timeout_s: int = 20,
    max_retries: int = 3,
) -> Tuple[int, str]:
    """POST JSON，网络/SSL 异常自动重试。"""
    ctx = ssl._create_unverified_context()
    body = _json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("content-type", "application/json")

    for attempt in range(max_retries):
        try:
            if opener is None:
                with urllib.request.urlopen(req, context=ctx, timeout=timeout_s) as r:
                    raw = r.read()
                    return r.status, raw.decode("utf-8", "ignore")
            with opener.open(req, timeout=timeout_s) as r:
                raw = r.read()
                return r.status, raw.decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            raw = b""
            try:
                raw = e.read()
            except Exception:
                pass
            return e.code, raw.decode("utf-8", "ignore")
        except (ssl.SSLError, urllib.error.URLError, OSError) as e:
            if attempt < max_retries - 1:
                wait_time = 0.5 * (2**attempt)
                logger.debug(
                    f"[_http_post_json] Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__}: {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                logger.warning(
                    f"[_http_post_json] All {max_retries} attempts failed. Last error: {type(e).__name__}: {e}"
                )
                raise


def _http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout_s: int = 15) -> Tuple[int, str]:
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, method="GET")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=timeout_s) as r:
            raw = r.read()
            return r.status, raw.decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        raw = b""
        try:
            raw = e.read()
        except Exception:
            pass
        return e.code, raw.decode("utf-8", "ignore")


def _abp_application_configuration(
    backend_url: str,
    *,
    access_token: Optional[str] = None,
    opener: Optional[urllib.request.OpenerDirector] = None,
) -> Tuple[bool, List[str], bool, str]:
    """拉取 ABP application-configuration 并提取 roles。"""
    url = f"{backend_url.rstrip('/')}/api/abp/application-configuration"
    headers = {"authorization": f"Bearer {access_token}"} if access_token else None
    if opener is None:
        st, body = _http_get(url, headers=headers, timeout_s=20)
    else:
        req = urllib.request.Request(url, method="GET")
        try:
            with opener.open(req, timeout=20) as r:
                raw = r.read()
                st, body = r.status, raw.decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            raw = b""
            try:
                raw = e.read()
            except Exception:
                pass
            st, body = e.code, raw.decode("utf-8", "ignore")
    if st != 200:
        return False, [], False, f"abp_cfg_status={st}"
    try:
        j = _json.loads(body)
        cu = j.get("currentUser") or {}
        authenticated = bool(cu.get("isAuthenticated"))
        roles = cu.get("roles") or []
        return True, [str(x) for x in roles], authenticated, "ok"
    except Exception:
        return False, [], False, "abp_cfg_parse_error"


def _classify_abp_login_result(body_text: str) -> str:
    """解析 /api/account/login 的 AbpLoginResult。"""
    try:
        j = _json.loads(body_text or "{}")
    except Exception:
        j = {}
    desc = str(j.get("description") or "")
    blob = desc.lower()
    if "invalidusernameorpassword" in blob:
        return "invalid_credentials"
    if "lockedout" in blob:
        return "lockout"
    if desc:
        return f"login_{desc}"
    return "login_unknown"


def _abp_cookie_login_and_roles(
    *,
    backend_url: str,
    identifier: str,
    password: str,
) -> Tuple[bool, str, List[str], bool]:
    """
    不依赖 OIDC client：
    1) POST /api/account/login（JSON）
    2) 复用 cookie GET /api/abp/application-configuration，读取 roles
    """
    login_url = f"{backend_url.rstrip('/')}/api/account/login"
    payload = {"userNameOrEmailAddress": identifier, "password": password, "rememberMe": False}

    if HAS_REQUESTS:
        try:
            import requests

            requests.packages.urllib3.disable_warnings()
            session = requests.Session()
            session.verify = False
            resp = session.post(login_url, json=payload, timeout=20)
            if resp.status_code != 200:
                return False, f"login_status={resp.status_code}", [], False

            body = resp.json()
            reason = _classify_abp_login_result(_json.dumps(body))
            if reason != "login_Success":
                return False, reason, [], False

            cfg_url = f"{backend_url.rstrip('/')}/api/abp/application-configuration"
            cfg_resp = session.get(cfg_url, timeout=20)
            if cfg_resp.status_code != 200:
                return False, f"abp_cfg_status={cfg_resp.status_code}", [], False

            cfg_data = cfg_resp.json()
            cu = cfg_data.get("currentUser") or {}
            authenticated = bool(cu.get("isAuthenticated"))
            roles = [str(x) for x in (cu.get("roles") or [])]
            if not authenticated:
                return False, "not_authenticated", roles, False
            return True, "ok", roles, True
        except Exception as e:
            logger.warning(
                f"[_abp_cookie_login_and_roles] requests failed: {type(e).__name__}: {e}, falling back to urllib"
            )

    ctx = ssl._create_unverified_context()
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPCookieProcessor(jar),
    )

    st, body = _http_post_json(login_url, payload, opener=opener, timeout_s=20)
    if st != 200:
        return False, f"login_status={st}", [], False

    reason = _classify_abp_login_result(body)
    if reason != "login_Success":
        return False, reason, [], False

    ok_cfg, roles, authenticated, reason_cfg = _abp_application_configuration(backend_url, opener=opener)
    if not ok_cfg:
        return False, reason_cfg, roles, authenticated
    if not authenticated:
        return False, "not_authenticated", roles, False
    return True, "ok", roles, True
