"""Module execution file"""
from dataclasses import dataclass
from pathlib import Path

import click
from click import Context

from modelserve.cli import serve
from modelserve.model_handlers import (
    TextTransformModelHandler,
    ModelHandler,
    ImageGenerateModelHandler,
)
from modelserve.request_handlers import (
    TextTransformRequestHandler,
    RequestHandler,
    ImageGenerateRequestHandler,
)


@dataclass
class Config:
    model_offload_folder: Path
    bind: list[str]
    access_log: str
    error_log: str


@click.group
@click.option(
    "--model-offload-folder",
    envvar="MODEL_OFFLOAD_FOLDER",
    help="Filesystem folder in which tensor data will be placed if the tensors cannot "
    "be stored fully in memory.",
    default=None,
    show_envvar=True,
)
@click.option(
    "--bind",
    envvar="SERVER_BIND",
    help="IP and port with which to bind the API web server. It must be in the form of "
    "<host>:<port>.",
    default="127.0.0.1:8000",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--access-log",
    envvar="SERVER_ACCESS_LOG",
    help='Location of API web server access log. "-" will send to STDOUT',
    default="-",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--error-log",
    envvar="SERVER_ERROR_LOG",
    help='Location of API web server error log. "-" will send to STDERR',
    default="-",
    show_default=True,
)
@click.pass_context
def main(
    ctx: Context,
    model_offload_folder: Path,
    bind: list[str],
    access_log: str,
    error_log: str,
):
    """
    Server a version of a model as an API

    MODEL_IDENTIFIER: Can be a path to the folder containing a built, cloned, or
    downloaded model. It can also be an identifier in the Huggingface Hub.

    MODEL_REVISION (optional): This is only relevant when MODEL_IDENTIFIER is an
    identifier in the Huggingface Hub. The revision will be a commit hash or tag to
    identify which revision of the model in the Huggingface Hub should be used. The
    latest version available will be utilized when not provided.
    """
    ctx.obj = Config(
        model_offload_folder=model_offload_folder,
        bind=bind,
        access_log=access_log,
        error_log=error_log,
    )


@main.command(name="text-transform")
@click.argument("MODEL_IDENTIFIER")
@click.argument("MODEL_REVISION", required=False, default=None)
@click.pass_obj
def text_transform(config: Config, model_identifier: str, model_revision: str | None):
    """Serve a text transform API with a text transform model"""
    call_serve(
        "Text transformation model service",
        TextTransformModelHandler,
        model_identifier,
        model_revision,
        TextTransformRequestHandler,
        config,
    )


@main.command(name="image-generate")
@click.argument("MODEL_IDENTIFIER")
@click.argument("MODEL_REVISION", required=False, default=None)
@click.pass_obj
def image_generation(config: Config, model_identifier: str, model_revision: str | None):
    """Serve an image generation API with an image generation model"""
    call_serve(
        "Image Generation Model Service",
        ImageGenerateModelHandler,
        model_identifier,
        model_revision,
        ImageGenerateRequestHandler,
        config,
    )


def call_serve(
    service_name,
    model_handler_class: type[ModelHandler],
    model_identifier: str,
    model_revision: str | None,
    request_handler_class: type[RequestHandler],
    config: Config,
):
    """Shared code to call serve"""
    serve(
        service_name=service_name,
        model_handler_class=model_handler_class,
        model_identifier=model_identifier,
        model_revision=model_revision,
        model_offload_folder=config.model_offload_folder,
        request_handler_class=request_handler_class,
        webserver_bind=config.bind,
        webserver_access_log=config.access_log,
        webserver_error_log=config.error_log,
    )


if __name__ == "__main__":
    main()
