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
