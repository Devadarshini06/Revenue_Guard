import asyncio
import json
import urllib.parse
from typing import Dict, Any, Optional, Tuple


class ASGIResponse:
    def __init__(self, status_code: int, headers: Dict[str, str], body: bytes):
        self.status_code = status_code
        self.headers = headers
        self.body = body

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.text)


class ASGITestClient:
    """
    Lightweight, zero-external-dependency test client for ASGI / FastAPI apps.
    Directly invokes app(scope, receive, send) using asyncio.
    """
    def __init__(self, app):
        self.app = app

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> ASGIResponse:
        return asyncio.run(self._async_request(method, path, params, json_data, data, headers))

    async def _async_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> ASGIResponse:
        parsed_url = urllib.parse.urlparse(path)
        raw_path = parsed_url.path

        # Handle query parameters
        query_string = parsed_url.query
        if params:
            encoded_params = urllib.parse.urlencode(
                [(k, v) for k, v in params.items() if v is not None]
            )
            if query_string:
                query_string = f"{query_string}&{encoded_params}"
            else:
                query_string = encoded_params

        # Prepare body
        body_bytes = b""
        req_headers = {
            b"host": b"testserver",
            b"user-agent": b"ASGITestClient/1.0"
        }
        if headers:
            for k, v in headers.items():
                req_headers[k.lower().encode("latin1")] = str(v).encode("latin1")

        if json_data is not None:
            body_bytes = json.dumps(json_data).encode("utf-8")
            req_headers[b"content-type"] = b"application/json"
            req_headers[b"content-length"] = str(len(body_bytes)).encode("latin1")
        elif data is not None:
            body_bytes = data
            req_headers[b"content-length"] = str(len(body_bytes)).encode("latin1")

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "http_version": "1.1",
            "method": method.upper(),
            "scheme": "http",
            "path": raw_path,
            "raw_path": raw_path.encode("latin1"),
            "query_string": query_string.encode("latin1"),
            "headers": [(k, v) for k, v in req_headers.items()],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }

        request_sent = False

        async def receive():
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {
                    "type": "http.request",
                    "body": body_bytes,
                    "more_body": False
                }
            # After the request body is sent, ASGI specs expect http.disconnect
            return {"type": "http.disconnect"}

        status_code = 500
        res_headers = {}
        res_body_chunks = []

        async def send(message):
            nonlocal status_code, res_headers, res_body_chunks
            if message["type"] == "http.response.start":
                status_code = message["status"]
                res_headers = {
                    k.decode("latin1"): v.decode("latin1")
                    for k, v in message.get("headers", [])
                }
            elif message["type"] == "http.response.body":
                res_body_chunks.append(message.get("body", b""))

        await self.app(scope, receive, send)

        return ASGIResponse(
            status_code=status_code,
            headers=res_headers,
            body=b"".join(res_body_chunks)
        )

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> ASGIResponse:
        return self.request("GET", path, params=params, **kwargs)

    def post(self, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Any] = None, **kwargs) -> ASGIResponse:
        return self.request("POST", path, params=params, json_data=json, **kwargs)

    def post_file(
        self,
        path: str,
        filename: str,
        file_bytes: bytes,
        field_name: str = "file",
        content_type: str = "text/csv",
        params: Optional[Dict[str, Any]] = None
    ) -> ASGIResponse:
        boundary = "----RevenueGuardBoundary9876543210"
        header_part = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8")
        footer_part = f"\r\n--{boundary}--\r\n".encode("utf-8")
        body = header_part + file_bytes + footer_part

        headers = {
            "content-type": f"multipart/form-data; boundary={boundary}"
        }
        return self.request("POST", path, params=params, data=body, headers=headers)

