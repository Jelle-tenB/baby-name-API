import pytest
from httpx import AsyncClient, ASGITransport
import time
import logging
from main import app

how_to_run = "pytest -n auto testing.py"

URL = "http://test"
transport = ASGITransport(app=app)

# Set up logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

@pytest.mark.asyncio
async def test_similar_names():
    total_time = 0
    runs = 10
    for i in range(runs):
        start = time.perf_counter()
        async with AsyncClient(transport=transport, base_url=URL) as client:
            response = await client.get("/similar", params={"name_id": [1, 2]})

        assert response.status_code == 200
        json_response = response.json()
        assert isinstance(json_response, list)
        assert all(isinstance(item, dict) for item in json_response)

        async with AsyncClient(transport=transport, base_url=URL) as client:
            resp1 = await client.get("/search", params={"letter": "a", "gender": "m", "country": "US", "start": 1})
        assert resp1.status_code == 200

        async with AsyncClient(transport=transport, base_url=URL) as client:
            resp2 = await client.get("/search", params={"letter": "1"})
        assert resp2.status_code == 422

        async with AsyncClient(transport=transport, base_url=URL) as client:
            resp3 = await client.get("/search", params={})
        assert resp3.status_code == 400

        end = time.perf_counter()
        duration = end - start
        logger.info("Run %d took %.4f seconds", i+1, duration)
        total_time += duration

    logger.info("Total time for %d runs: %.4f seconds", runs, total_time)
    logger.info("Average time per run: %.4f seconds", total_time/runs)
