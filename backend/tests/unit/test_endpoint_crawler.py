import httpx

from pentest_platform.adapters.tools.endpoint_crawler import EndpointCrawler


def test_crawler_retries_root_500_then_continues_to_fallbacks_and_links():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/":
            return httpx.Response(500, json={"error": "root broken"})
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/docs":
            return httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text='<html><a href="/about">About</a><a href="https://other.example.net/x">x</a></html>',
            )
        if request.url.path == "/about":
            return httpx.Response(200, headers={"content-type": "text/html"}, text="<html>ok</html>")
        return httpx.Response(404)

    result = EndpointCrawler(transport=httpx.MockTransport(handler)).crawl(
        base_url="https://example.com",
        targets=["example.com"],
        exclusions=[],
        max_pages=12,
        max_requests=40,
    )
    paths = {item["path"] for item in result["endpoints"]}
    assert "/" in paths
    assert "/health" in paths
    assert "/about" in paths
    assert "/x" not in paths
    assert calls.count("/") == 3
    assert any(item["path"] == "/" and item.get("error") for item in result["endpoints"])


def test_crawler_extracts_openapi_methods_and_parameters():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/openapi.json":
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                json={
                    "openapi": "3.0.0",
                    "paths": {
                        "/v1/users": {
                            "get": {"parameters": [{"name": "limit"}]},
                            "post": {"parameters": [{"name": "role"}]},
                        },
                        "/v1/users/{id}": {"delete": {}},
                    },
                },
            )
        return httpx.Response(404)

    result = EndpointCrawler(transport=httpx.MockTransport(handler)).crawl(
        base_url="https://example.com",
        targets=["example.com"],
        exclusions=[],
        max_pages=20,
        max_requests=30,
    )
    by_path = {item["path"]: item for item in result["endpoints"]}
    assert by_path["/v1/users"]["methods"] == ["GET", "POST"]
    assert by_path["/v1/users"]["parameters"] == ["limit", "role"]
    assert by_path["/v1/users/{id}"]["methods"] == ["DELETE"]


def test_each_crawler_retry_reserves_budget_and_checks_controls():
    reservations = []
    calls = []
    def guard():
        reservations.append(True)
        return len(reservations) <= 2
    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(503)
    result = EndpointCrawler(transport=httpx.MockTransport(handler)).crawl(
        base_url="https://example.com", targets=["example.com"], exclusions=[],
        max_requests=20, request_delay_seconds=0, request_guard=guard,
    )
    assert len(calls) == result["requests"] == 2
    assert len(reservations) == 3
    assert result["truncated"]


def test_crawler_extracts_js_origins_cookies_redirects_and_soft_404():
    root_body = '<html><div id="root"></div><a href="/redirect">go</a><script src="/app.js"></script></html>'
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(200, headers={"content-type": "text/html", "set-cookie": "sid=abc; Path=/; Secure; HttpOnly; SameSite=None"}, text=root_body)
        if request.url.path == "/api/v1":
            return httpx.Response(200, headers={"content-type": "text/html"}, text=root_body)
        if request.url.path == "/app.js":
            return httpx.Response(200, headers={"content-type": "application/javascript"}, text='fetch("https://api.example.com/api/v1/me"); fetch("/api/v1/refresh")')
        if request.url.path == "/redirect":
            return httpx.Response(302, headers={"location": "/next"})
        if request.url.path == "/next":
            return httpx.Response(200, headers={"content-type": "text/html"}, text="<html>next</html>")
        return httpx.Response(404)

    result = EndpointCrawler(transport=httpx.MockTransport(handler)).crawl(
        base_url="https://example.com",
        targets=["example.com"],
        exclusions=[],
        max_pages=20,
        max_requests=40,
    )
    paths = {item["path"] for item in result["endpoints"]}
    assert "/next" in paths
    assert "/api/v1" not in paths
    assert "/api/v1/refresh" in paths
    assert result["external_origins"][0]["host"] == "api.example.com"
    assert result["external_origins"][0]["sample_paths"] == ["/api/v1/me"]
    root = next(item for item in result["endpoints"] if item["path"] == "/")
    assert root["cookies"][0]["name"] == "sid"
    assert root["cookies"][0]["secure"] is True
    assert root["cookies"][0]["httponly"] is True
