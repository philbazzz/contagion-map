"""Small HTTP client with timeout, retry/backoff and typed errors.

Error messages never include URLs or headers, so API keys cannot leak into
logs or API responses.
"""
from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from typing import Callable, Optional


class FetchError(Exception):
    code = "fetch_error"

    def __init__(self, detail: str = "", retry_after: Optional[float] = None):
        super().__init__(detail)
        self.detail = detail
        self.retry_after = retry_after


class NoKey(FetchError):
    code = "no_key"


class AuthError(FetchError):
    code = "auth_error"


class RateLimited(FetchError):
    code = "rate_limited"


class TimeoutErr(FetchError):
    code = "timeout"


class NetworkError(FetchError):
    code = "network_error"


class BadResponse(FetchError):
    code = "bad_response"


Transport = Callable[[str, str, dict, Optional[bytes], float], tuple]


def urllib_transport(method: str, url: str, headers: dict, body: Optional[bytes], timeout: float):
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read() if e.fp else b""


def request_json(method: str, url: str, *, headers: Optional[dict] = None, payload=None,
                 timeout: float = 15.0, retries: int = 3, transport: Transport = urllib_transport,
                 auth_statuses=(401, 403), sleep=time.sleep):
    body = json.dumps(payload).encode() if payload is not None else None
    hdrs = {"Accept": "application/json", "User-Agent": "contagion-market/0.2"}
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    hdrs.update(headers or {})
    last: Optional[FetchError] = None
    for attempt in range(retries):
        try:
            status, resp_headers, raw = transport(method, url, hdrs, body, timeout)
        except (socket.timeout, TimeoutError):
            last = TimeoutErr(f"응답 시간 초과 ({timeout:.0f}초)")
        except urllib.error.URLError as e:
            reason = getattr(e, "reason", "")
            last = TimeoutErr("응답 시간 초과") if isinstance(reason, socket.timeout) else NetworkError("네트워크 연결 실패")
        except OSError:
            last = NetworkError("네트워크 연결 실패")
        else:
            if status in auth_statuses:
                raise AuthError(f"인증 실패 (HTTP {status}) — API 키를 확인하세요")
            if status == 429:
                ra = resp_headers.get("Retry-After") or resp_headers.get("retry-after")
                try:
                    ra_s = float(ra) if ra else None
                except ValueError:
                    ra_s = None
                raise RateLimited("호출 한도 초과 (HTTP 429)", retry_after=ra_s)
            if 500 <= status < 600:
                last = BadResponse(f"제공처 서버 오류 (HTTP {status})")
            elif status >= 400:
                text = raw[:300].decode("utf-8", "replace")
                if "api_key" in text.lower() or "invalid user key" in text.lower():
                    raise AuthError(f"인증 실패 (HTTP {status}) — API 키를 확인하세요")
                raise BadResponse(f"요청 오류 (HTTP {status})")
            else:
                try:
                    return json.loads(raw.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    raise BadResponse("응답 형식 오류 (JSON 아님)")
        if attempt < retries - 1:
            sleep(min(8.0, 1.5 * (2 ** attempt)))
    raise last or NetworkError("알 수 없는 오류")
