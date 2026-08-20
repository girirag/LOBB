import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data


@pytest.mark.asyncio
async def test_shorten_url_auto_code(client: AsyncClient):
    original_url = "https://www.example.com/very/long/path/with?query=params"
    response = await client.post(
        "/shorten",
        json={"url": original_url}
    )
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert len(data["short_code"]) == 6
    assert data["original_url"] == original_url
    assert data["short_url"].endswith(data["short_code"])


@pytest.mark.asyncio
async def test_shorten_url_custom_code(client: AsyncClient):
    original_url = "https://news.ycombinator.com/"
    custom_code = "my-hn-link"
    response = await client.post(
        "/shorten",
        json={"url": original_url, "custom_code": custom_code}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["short_code"] == custom_code
    assert data["original_url"] == original_url
    assert data["short_url"].endswith(f"/{custom_code}")


@pytest.mark.asyncio
async def test_shorten_duplicate_custom_code_conflict(client: AsyncClient):
    payload = {
        "url": "https://fastapi.tiangolo.com",
        "custom_code": "fastapi-docs"
    }
    # First creation should succeed
    res1 = await client.post("/shorten", json=payload)
    assert res1.status_code == 201

    # Second creation with identical custom code should return 409
    res2 = await client.post("/shorten", json=payload)
    assert res2.status_code == 409
    assert "already taken" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_shorten_invalid_url_fails(client: AsyncClient):
    response = await client.post(
        "/shorten",
        json={"url": "not-a-valid-url"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_shorten_invalid_custom_code_fails(client: AsyncClient):
    # Custom code with illegal character (e.g. space or @)
    response = await client.post(
        "/shorten",
        json={"url": "https://example.com", "custom_code": "invalid code!"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_redirect_to_original_url(client: AsyncClient):
    original_url = "https://github.com/tiangolo/fastapi"
    # Create short URL
    create_res = await client.post(
        "/shorten",
        json={"url": original_url, "custom_code": "fastapi-repo"}
    )
    assert create_res.status_code == 201
    short_code = create_res.json()["short_code"]

    # Request redirect without following it automatically
    redirect_res = await client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_res.status_code == 307
    assert redirect_res.headers["location"] == original_url


@pytest.mark.asyncio
async def test_redirect_increments_clicks_and_stats(client: AsyncClient):
    original_url = "https://python.org"
    create_res = await client.post(
        "/shorten",
        json={"url": original_url}
    )
    short_code = create_res.json()["short_code"]

    # Initial stats -> 0 clicks
    stats1 = await client.get(f"/stats/{short_code}")
    assert stats1.status_code == 200
    assert stats1.json()["clicks"] == 0

    # Perform 3 redirects
    for _ in range(3):
        await client.get(f"/{short_code}", follow_redirects=False)

    # Updated stats -> 3 clicks
    stats2 = await client.get(f"/stats/{short_code}")
    assert stats2.status_code == 200
    assert stats2.json()["clicks"] == 3


@pytest.mark.asyncio
async def test_redirect_not_found(client: AsyncClient):
    response = await client.get("/nonexistent123", follow_redirects=False)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_stats_not_found(client: AsyncClient):
    response = await client.get("/stats/nonexistent123")
    assert response.status_code == 404
