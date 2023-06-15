import asyncio
import queue
from asyncio import Future
import multiprocessing as mp
from typing import Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel

from modelserve.models import (
    TextTransformRequest,
    TextTransformResponse,
    ImageGenerateRequest,
    ImageGenerateResponse,
)

T1 = TypeVar("T1")
T2 = TypeVar("T2")


class RequestHandler(Generic[T1, T2]):
    """
    Callable class that handles sending requests to and receiving responses from the
    model handler's process
    """

    def __init__(
        self,
        request_queue: mp.Queue,
        request_future_map: dict[UUID, Future[T2]],
    ) -> None:
        self._request_queue = request_queue
        self._request_future_map = request_future_map

    async def __call__(self, request: T1) -> T2:
        future: Future[BaseModel] = asyncio.get_running_loop().create_future()
        request_id = uuid4()
        self._request_future_map[request_id] = future
        sent = False
        while not sent:
            try:
                self._request_queue.put((request_id, request), block=False)
                sent = True
            except queue.Full:
                await asyncio.sleep(0)
        return await future


class ImageGenerateRequestHandler(RequestHandler):
    """
    Class necessary to properly generate request/response OpenAPI docs.
    Just acts as a passthrough.
    """

    async def __call__(self, request: ImageGenerateRequest) -> ImageGenerateResponse:
        return await super().__call__(request)


class TextTransformRequestHandler(RequestHandler):
    """
    Class necessary to properly generate request/response OpenAPI docs.
    Just acts as a passthrough.
    """

    async def __call__(self, request: TextTransformRequest) -> TextTransformResponse:
        return await super().__call__(request)
