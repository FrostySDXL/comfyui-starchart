import json
import random
import time
from ssl import SSLContext
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_SECONDS = 0.5
DEFAULT_RETRY_MULTIPLIER = 2
DEFAULT_RETRY_TOTAL_CAP_SECONDS = 5.0
RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


class RetryBudgetExceeded(RuntimeError):
    """Raised when bounded retry attempts or backoff budget are exhausted."""


def _content_type(response) -> str:
    headers = getattr(response, "headers", None)
    if headers is None:
        return "unknown"
    get_content_type = getattr(headers, "get_content_type", None)
    if callable(get_content_type):
        return str(get_content_type())
    get = getattr(headers, "get", None)
    if callable(get):
        return str(get("Content-Type", "unknown"))
    return "unknown"


def _retry_delay(attempt: int) -> float:
    upper_bound = DEFAULT_RETRY_BASE_SECONDS * (DEFAULT_RETRY_MULTIPLIER**attempt)
    return random.uniform(0, upper_bound)


def _urlopen(request_or_url, timeout: int, ssl_context: SSLContext | None):
    if ssl_context is not None:
        return urlopen(request_or_url, timeout=timeout, context=ssl_context)
    return urlopen(request_or_url, timeout=timeout)


def _open_with_retries(request_or_url, timeout: int, ssl_context: SSLContext | None, retry: bool):
    attempts = DEFAULT_MAX_RETRIES if retry else 1
    cumulative_delay = 0.0
    last_error: HTTPError | None = None

    for attempt_index in range(attempts):
        try:
            return _urlopen(request_or_url, timeout, ssl_context)
        except HTTPError as exc:
            last_error = exc
            if not retry or exc.code not in RETRYABLE_STATUS_CODES:
                raise
            if attempt_index >= attempts - 1:
                raise RetryBudgetExceeded(
                    f"Retry budget exhausted after {attempts} attempts; last HTTP error {exc.code}"
                ) from exc
            delay = _retry_delay(attempt_index + 1)
            if cumulative_delay + delay > DEFAULT_RETRY_TOTAL_CAP_SECONDS:
                raise RetryBudgetExceeded(
                    f"Retry backoff budget exceeded before next attempt; last HTTP error {exc.code}"
                ) from exc
            cumulative_delay += delay
            time.sleep(delay)

    if last_error is not None:
        raise RetryBudgetExceeded("Retry budget exhausted") from last_error
    raise RetryBudgetExceeded("Retry budget exhausted")


def _read_json_response(
    request_or_url,
    timeout: int,
    max_bytes: int = DEFAULT_MAX_BYTES,
    ssl_context: SSLContext | None = None,
    retry: bool = False,
) -> tuple[object, bytes, str]:
    url = getattr(request_or_url, "full_url", request_or_url)
    try:
        with _open_with_retries(request_or_url, timeout, ssl_context, retry) as response:
            raw_bytes = response.read(max_bytes + 1)
            content_type = _content_type(response)
    except HTTPError as exc:
        raise RuntimeError(f"HTTP error {exc.code} from {url}: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"URL error reaching {url}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError(f"Timeout reaching {url} after {timeout}s") from exc

    if len(raw_bytes) > max_bytes:
        raise RuntimeError(f"Response from {url} exceeds {max_bytes} byte limit")

    try:
        payload = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from {url} (content-type {content_type}): {exc}") from exc

    return payload, raw_bytes, str(url)


def get_json(
    url: str,
    timeout: int = 30,
    headers: dict | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    ssl_context: SSLContext | None = None,
) -> object:
    request = Request(url, headers=headers or {"Accept": "application/json"})
    payload, _, _ = _read_json_response(
        request, timeout, max_bytes=max_bytes, ssl_context=ssl_context, retry=True
    )
    return payload


def get_json_with_bytes(
    url: str,
    timeout: int = 30,
    headers: dict | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    ssl_context: SSLContext | None = None,
) -> tuple[object, bytes]:
    request = Request(url, headers=headers or {"Accept": "application/json"})
    payload, raw_bytes, _ = _read_json_response(
        request, timeout, max_bytes=max_bytes, ssl_context=ssl_context, retry=True
    )
    return payload, raw_bytes


def post_json(
    url: str,
    payload: dict,
    timeout: int = 30,
    headers: dict | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    ssl_context: SSLContext | None = None,
    retry: bool = False,
) -> object:
    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if headers:
        request_headers.update(headers)
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    response_payload, _, _ = _read_json_response(
        request, timeout, max_bytes=max_bytes, ssl_context=ssl_context, retry=retry
    )
    return response_payload
