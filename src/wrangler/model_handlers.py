"""Model Handlers"""
import abc
import base64
import multiprocessing as mp
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import UUID

import click
import torch
from PIL.Image import Image
from diffusers import DiffusionPipeline
from transformers import AutoTokenizer, AutoModelForCausalLM

from wrangler.models import (
    ImageGenerateRequest,
    ImageGenerateResponse,
    TextTransformRequest,
    TextTransformResponse,
    ImageFormat,
)


class RunInput(abc.ABC):
    """Base class for run input"""

    pass


@dataclass(frozen=True)
class RunGenerateInput(RunInput):
    """Input data for running a generate command"""

    input: str


@dataclass(frozen=True)
class RunImageGenerateInput(RunGenerateInput):
    """Input data for running a generate image command"""

    output_file: Path


class ModelHandler(abc.ABC):
    """Abstract base class for handlers"""

    @abc.abstractmethod
    def start(self, request_queue: mp.Queue, response_queue: mp.Queue) -> None:
        """
        Initialize the model and begin processing requests
        :param request_queue: Queue to send requests to be processed
        :param response_queue: Queue in which responses will be placed
        """
        raise NotImplementedError

    @abc.abstractmethod
    def run(self, input_: RunInput) -> None:
        """
        Initialize the model and process a single request
        :param input_: Input for the run request
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def create(
        cls,
        model: str,
        revision: str | None,
        offload_folder: str | None,
    ) -> "ModelHandler":
        """Standard factory method for all handlers"""
        raise NotImplementedError


class ImageGenerateModelHandler(ModelHandler):
    """
    Handler for initializing an image generation model pipeline and then executing
    requests against the pipeline.
    """

    def __init__(
        self,
        model: str,
        revision: str | None,
    ):
        self._model = model
        self._revision = revision

    def _get_pipeline(self) -> DiffusionPipeline:
        pipeline = DiffusionPipeline.from_pretrained(self._model, revision=self._revision)
        pipeline = pipeline.to("cuda") if torch.cuda.is_available() else pipeline
        return pipeline

    @staticmethod
    def _generate_image(pipeline, input_: str) -> Image:
        result = pipeline(input_)
        image: Image = result.images[0]
        return image

    @staticmethod
    def _get_image_base64(image: Image, output_format: ImageFormat):
        image_bytes_io = BytesIO()
        image.save(image_bytes_io, format=output_format.value)
        image_bytes = image_bytes_io.getvalue()
        image_base64 = base64.b64encode(image_bytes).decode()
        return image_base64

    def start(self, request_queue: mp.Queue, response_queue: mp.Queue) -> None:
        pipeline = self._get_pipeline()
        while True:
            item: tuple[UUID, ImageGenerateRequest] = request_queue.get()
            request_id, request = item
            try:
                image = self._generate_image(pipeline, request.input)
                image_base64 = self._get_image_base64(image, request.format)
                response: ImageGenerateResponse | Exception = ImageGenerateResponse(
                    image=image_base64, format=request.format
                )
            except Exception as e:
                response = e
            response_queue.put((request_id, response))

    def run(self, input_: RunImageGenerateInput) -> None:  # type: ignore[override]
        pipeline = self._get_pipeline()
        image = self._generate_image(pipeline, input_.input)
        with input_.output_file.open("wb") as output_file:
            image.save(output_file)

    @classmethod
    def create(
        cls,
        model: str,
        revision: str | None,
        offload_folder: str | None,
    ) -> "ImageGenerateModelHandler":
        return cls(model, revision)


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
    ):
        self._model = model
        self._revision = revision
        self._offload_folder = offload_folder

    def _get_model_and_tokenizer(self):
        tokenizer = AutoTokenizer.from_pretrained(self._model, revision=self._revision)
        model = AutoModelForCausalLM.from_pretrained(
            self._model,
            revision=self._revision,
            device_map="auto",
            offload_folder=self._offload_folder,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.bfloat16,
        )
        return model, tokenizer

    @staticmethod
    def _generate_results(model, tokenizer, input_):
        tensor = tokenizer(input_, return_tensors="pt", return_token_type_ids=False).to(
            model.device
        )
        outputs = model.generate(
            **tensor,
            early_stopping=True,
        )
        results = [tokenizer.decode(output, skip_special_tokens=True) for output in outputs]
        return results

    def start(self, request_queue: mp.Queue, response_queue: mp.Queue) -> None:
        model, tokenizer = self._get_model_and_tokenizer()
        while True:
            item: tuple[UUID, TextTransformRequest] = request_queue.get()
            request_id, request = item
            try:
                results = self._generate_results(model, tokenizer, request.input)

                response: TextTransformResponse | Exception = TextTransformResponse(
                    generated_text=results[0]
                )
            except Exception as e:
                response = e
            response_queue.put((request_id, response))

    def run(self, input_: RunGenerateInput) -> None:  # type: ignore[override]
        model, tokenizer = self._get_model_and_tokenizer()
        results = self._generate_results(model, tokenizer, input_.input)
        click.secho(results[0], italic=True)

    @classmethod
    def create(
        cls,
        model: str,
        revision: str | None,
        offload_folder: str | None,
    ) -> "TextTransformModelHandler":
        return cls(model, revision, offload_folder)
