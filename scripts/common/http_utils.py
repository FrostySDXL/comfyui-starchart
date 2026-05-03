import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _read_json_response(request_or_url, timeout: int) -> tuple[object, bytes, str]:
    url = getattr(request_or_url, "full_url", request_or_url)
    try:
        with urlopen(request_or_url, timeout=timeout) as response:
            raw_bytes = response.read()
    except HTTPError as exc:
        raise RuntimeError(f"HTTP error {exc.code} from {url}: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"URL error reaching {url}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError(f"Timeout reaching {url} after {timeout}s") from exc

    try:
        payload = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from {url}: {exc}") from exc

    return payload, raw_bytes, str(url)


def get_json(url: str, timeout: int = 30, headers: dict | None = None) -> object:
    request = Request(url, headers=headers or {"Accept": "application/json"})
    payload, _, _ = _read_json_response(request, timeout)
    return payload


def get_json_with_bytes(url: str, timeout: int = 30, headers: dict | None = None) -> tuple[object, bytes]:
    request = Request(url, headers=headers or {"Accept": "application/json"})
    payload, raw_bytes, _ = _read_json_response(request, timeout)
    return payload, raw_bytes


def post_json(url: str, payload: dict, timeout: int = 30, headers: dict | None = None) -> object:
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
    response_payload, _, _ = _read_json_response(request, timeout)
    return response_payload
