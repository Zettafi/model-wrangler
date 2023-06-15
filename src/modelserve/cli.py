import asyncio
import contextlib
import multiprocessing as mp
import queue
from asyncio import Future
from uuid import UUID

from hypercorn import Config as HypercornConfig
from hypercorn.asyncio import serve as hypercorn_serve
from fastapi import FastAPI
from pydantic import BaseModel

from . import __version__ as version
from .model_handlers import ModelHandler
from .request_handlers import RequestHandler


async def __responder(response_queue: mp.Queue, request_future_map_: dict[UUID, Future[BaseModel]]):
    while True:
        try:
            request_id, response = response_queue.get(block=False)
            future = request_future_map_[request_id]
            if isinstance(response, Exception):
                future.set_exception(response)
            else:
                future.set_result(response)
        except queue.Empty:
            await asyncio.sleep(0)


def serve(
    service_name: str,
    model_handler_class: type[ModelHandler],
    request_handler_class: type[RequestHandler],
    model_identifier: str,
    model_revision: str | None,
    model_offload_folder,
    webserver_bind,
    webserver_access_log,
    webserver_error_log,
):
    """Serve a model via an API"""
    model_request_queue: mp.Queue = mp.Queue()
    model_response_queue: mp.Queue = mp.Queue()
    model_handler = model_handler_class.create(
        model=model_identifier,
        revision=model_revision,
        offload_folder=model_offload_folder,
        request_queue=model_request_queue,
        response_queue=model_response_queue,
    )

    request_future_map: dict[UUID, Future[BaseModel]] = {}

    model_request_handler = request_handler_class(model_request_queue, request_future_map)

    @contextlib.asynccontextmanager
    async def lifespan(_app: FastAPI):
        """FastAPI lifespan manages the threadpool executor"""
        p = mp.Process(target=model_handler.start, name="Model Request Processor")
        p.start()
        responder_task = asyncio.get_event_loop().create_task(
            __responder(model_response_queue, request_future_map)
        )
        yield
        p.terminate()
        responder_task.cancel("Application shutting down")

    app = FastAPI(
        lifespan=lifespan,
        title=f"{service_name} ({model_identifier}:{model_revision if model_revision else 'HEAD'})",
        version=version,
        description=f"**{service_name}:**\n\n"
        f"Model: {model_identifier}\n\n"
        f"Revision: {model_revision}\n\n"
        f"Handler Class: {model_handler_class.__module__}.{model_handler_class.__name__}",
    )

    # noinspection PyTypeChecker
    app.add_api_route("/", model_request_handler.__call__, methods=["POST"], tags=["Models"])

    @app.get("/ping", status_code=204, tags=["Checks"])
    async def ping() -> None:
        """
        Is the service running
        """
        return

    config = HypercornConfig()
    config.bind = webserver_bind
    config.accesslog = webserver_access_log
    # noinspection SpellCheckingInspection
    config.errorlog = webserver_error_log
    # noinspection PyTypeChecker
    asyncio.run(hypercorn_serve(app, config))
