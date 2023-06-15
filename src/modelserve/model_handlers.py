import abc
import base64
import multiprocessing as mp
from io import BytesIO
from uuid import UUID

import torch
from PIL.Image import Image
from diffusers import DiffusionPipeline
from transformers import AutoTokenizer, AutoModelForCausalLM

from modelserve.models import (
    ImageGenerateRequest,
    ImageGenerateResponse,
    TextTransformRequest,
    TextTransformResponse,
)


class ModelHandler(abc.ABC):
    """Abstract base class for handlers"""

    @abc.abstractmethod
    def start(self) -> None:
        """Initialize the model and begin processing requests"""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def create(
        cls,
        model: str,
        revision: str | None,
        offload_folder: str | None,
        request_queue: mp.Queue,
        response_queue: mp.Queue,
    ) -> "ModelHandler":
        """Standard factory method for all handlers"""
        raise NotImplementedError


class ImageGenerateModelHandler(ModelHandler):
    """
    Handler for initializing a text transform model and then executing transform
    requests against the model.
    """

    def __init__(
        self,
        model: str,
        revision: str | None,
        request_queue: mp.Queue,
        response_queue: mp.Queue,
    ):
        self._model = model
        self._revision = revision
        self._request_queue = request_queue
        self._response_queue = response_queue

    def start(self) -> None:
        """
        Generate an image response based on the provided request
        """
        diffuser = DiffusionPipeline.from_pretrained(self._model, revision=self._revision)
        generator = diffuser.to("cuda") if torch.cuda.is_available() else diffuser
        while True:
            item: tuple[UUID, ImageGenerateRequest] = self._request_queue.get()
            request_id, request = item
            try:
                result = generator(request.input)
                image: Image = result.images[0]
                image_bytes_io = BytesIO()
                image.save(image_bytes_io, format=request.format.value)
                image_bytes = image_bytes_io.getvalue()
                image_base64 = base64.b64encode(image_bytes).decode()
                response: ImageGenerateResponse | Exception = ImageGenerateResponse(
                    image=image_base64, format=request.format
                )
            except Exception as e:
                response = e
            self._response_queue.put((request_id, response))

    @classmethod
    def create(
        cls,
        model: str,
        revision: str | None,
        offload_folder: str | None,
        request_queue: mp.Queue,
        response_queue: mp.Queue,
    ) -> "ImageGenerateModelHandler":
        return cls(model, revision, request_queue, response_queue)


class TextTransformModelHandler(ModelHandler):
    """
    Handler for initializing a text transform model and then executing transform
    requests against the model.
    """

    def __init__(
        self,
        model: str,
        revision: str | None,
        offload_folder: str | None,
        request_queue: mp.Queue,
        response_queue: mp.Queue,
    ):
        self._model = model
        self._revision = revision
        self._offload_folder = offload_folder
        self._request_queue = request_queue
        self._response_queue = response_queue

    def start(self) -> None:
        """
        Generate a transform response based on the provided input
        """
        tokenizer = AutoTokenizer.from_pretrained(self._model, revision=self._revision)
        model = AutoModelForCausalLM.from_pretrained(
            self._model,
            revision=self._revision,
            device_map="auto",
            offload_folder=self._offload_folder,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.bfloat16,
        )
        while True:
            item: tuple[UUID, TextTransformRequest] = self._request_queue.get()
            request_id, request = item
            try:
                tensor = tokenizer(
                    request.input, return_tensors="pt", return_token_type_ids=False
                ).to(model.device)

                outputs = model.generate(
                    **tensor,
                    early_stopping=True,
                )

                results = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]

                response: TextTransformResponse | Exception = TextTransformResponse(
                    generated_text=results[0]
                )
            except Exception as e:
                response = e
            self._response_queue.put((request_id, response))

    @classmethod
    def create(
        cls,
        model: str,
        revision: str | None,
        offload_folder: str | None,
        request_queue: mp.Queue,
        response_queue: mp.Queue,
    ) -> "TextTransformModelHandler":
        return cls(model, revision, offload_folder, request_queue, response_queue)
