"""Tests for async-safe request context."""

import asyncio

from aurarisk.core.context import (
    create_request_context,
    get_correlation_id,
    get_request_id,
    request_context,
)


def test_invalid_inbound_identifier_is_replaced() -> None:
    context = create_request_context(
        inbound_request_id="bad request id\n",
    )

    assert context.request_id != "bad request id\n"
    assert len(context.request_id) == 32
    assert context.correlation_id == context.request_id


def test_context_is_cleared_after_use() -> None:
    context = create_request_context("req-100", "corr-100")

    with request_context(context):
        assert get_request_id() == "req-100"
        assert get_correlation_id() == "corr-100"

    assert get_request_id() is None
    assert get_correlation_id() is None


def test_concurrent_requests_do_not_share_context() -> None:
    async def worker(identifier: str) -> str | None:
        context = create_request_context(
            identifier,
            identifier,
        )

        with request_context(context):
            # Force task interleaving.
            await asyncio.sleep(0)
            return get_request_id()

    async def run_workers() -> list[str | None]:
        return await asyncio.gather(
            worker("request-a"),
            worker("request-b"),
        )

    results = asyncio.run(run_workers())

    assert results == ["request-a", "request-b"]
