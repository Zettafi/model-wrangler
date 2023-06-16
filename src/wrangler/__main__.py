"""Module execution file"""

import pathlib
import typing as t
from dataclasses import dataclass

import click
from click import Context, ParamType, Parameter

from wrangler.cli import (
    serve as cli_serve,
    run as cli_run,
    run_image_generate as cli_run_image,
)
from wrangler.model_handlers import (
    TextTransformModelHandler,
    ImageGenerateModelHandler,
)
from wrangler.request_handlers import (
    TextTransformRequestHandler,
    ImageGenerateRequestHandler,
)


@dataclass(frozen=True)
class ModelIdentifier:
    """Identifier attributes for a model"""

    model: str
    revision: str | None


class ModelIdentifierType(ParamType):
    """ParamType for converting a model identifier string into a ModelIdentifier Object"""

    def convert(
        self, value: str, param: t.Optional[Parameter], ctx: t.Optional[Context]
    ) -> ModelIdentifier:
        identifier_parts = value.split(":", 1)
        return ModelIdentifier(
            model=identifier_parts[0],
            revision=identifier_parts[1] if len(identifier_parts) > 1 else None,
        )


@dataclass
class ServeConfig:
    """Config data for serving models"""

    service_name: str
    bind: list[str]
    access_log: str
    error_log: str


@click.group(name="wrangler")
def main():
    """
    Server a version of a model as an API

    MODEL_IDENTIFIER: Can be a path to the folder containing a built, cloned, or
    downloaded model. It can also be an identifier in the Huggingface Hub.

    MODEL_REVISION (optional): This is only relevant when MODEL_IDENTIFIER is an
    identifier in the Huggingface Hub. The revision will be a commit hash or tag to
    identify which revision of the model in the Huggingface Hub should be used. The
    latest version available will be utilized when not provided.
    """


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
    show_envvar=True,
)
@click.option(
    "--service-name",
    envvar="SERVER_SERVICE_NAME",
    help="Name of service to provide for OpenAPI docs",
    default=None,
    show_default=False,
    show_envvar=True,
)
@main.group(name="serve")
@click.pass_context
def serve(
    ctx: Context,
    service_name: str,
    bind: list[str],
    access_log: str,
    error_log: str,
):
    """Serve a model"""
    ctx.obj = ServeConfig(
        service_name=service_name, bind=bind, access_log=access_log, error_log=error_log
    )


@main.group(name="run")
def run():
    """Run the model for a single response"""
    pass


@serve.command(name="text-transform")
@click.argument("MODEL_IDENTIFIER", type=ModelIdentifierType())
@click.option(
    "--model-offload-folder",
    envvar="MODEL_OFFLOAD_FOLDER",
    help="Filesystem folder in which tensor data will be placed if the tensors cannot "
    "be stored fully in memory.",
    default=None,
    show_envvar=True,
    type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path),
)
@click.pass_obj
def text_transform_serve(
    config: ServeConfig,
    model_identifier: ModelIdentifier,
    model_offload_folder: str | None,
):
    """Text transform model action"""

    cli_serve(
        service_name=config.service_name if config.service_name else "Text Transform Model Service",
        model_handler_class=TextTransformModelHandler,
        model_identifier=model_identifier.model,
        model_revision=model_identifier.revision,
        model_offload_folder=model_offload_folder,
        request_handler_class=TextTransformRequestHandler,
        webserver_bind=config.bind,
        webserver_access_log=config.access_log,
        webserver_error_log=config.error_log,
    )


@run.command(name="text-transform")
@click.argument("MODEL_IDENTIFIER", type=ModelIdentifierType())
@click.argument("INPUT_TEXT", nargs=-1, required=True)
@click.option(
    "--model-offload-folder",
    envvar="MODEL_OFFLOAD_FOLDER",
    help="Filesystem folder in which tensor data will be placed if the tensors cannot "
    "be stored fully in memory.",
    default=None,
    show_envvar=True,
    type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path),
)
def text_transform_run(
    model_identifier: ModelIdentifier,
    model_offload_folder: str | None,
    input_text: list[str],
):
    """Text transform model action"""

    cli_run(
        model_handler_class=TextTransformModelHandler,
        model_identifier=model_identifier.model,
        model_revision=model_identifier.revision,
        model_offload_folder=model_offload_folder,
        input_text=" ".join(input_text),
    )


@serve.command(name="image-generate")
@click.argument("MODEL_IDENTIFIER", type=ModelIdentifierType())
@click.pass_obj
def image_generation_serve(
    config: ServeConfig,
    model_identifier: ModelIdentifier,
):
    """Serve an image generation API with an image generation model"""
    cli_serve(
        service_name="Image Generation Model Service"
        if config.service_name is None
        else config.service_name,
        model_handler_class=ImageGenerateModelHandler,
        request_handler_class=ImageGenerateRequestHandler,
        model_identifier=model_identifier.model,
        model_revision=model_identifier.revision,
        model_offload_folder=None,
        webserver_bind=config.bind,
        webserver_access_log=config.access_log,
        webserver_error_log=config.error_log,
    )


@run.command(name="image-generate")
@click.argument("MODEL_IDENTIFIER", type=ModelIdentifierType())
@click.argument(
    "DESTINATION_FILE",
    type=click.Path(file_okay=True, dir_okay=False, path_type=pathlib.Path),
)
@click.argument("INPUT_TEXT", required=True, nargs=-1)
def image_generation_run(
    model_identifier: ModelIdentifier,
    destination_file: pathlib.Path,
    input_text: list[str],
):
    """Serve an image generation API with an image generation model"""
    cli_run_image(
        model_handler_class=ImageGenerateModelHandler,
        model_identifier=model_identifier.model,
        model_revision=model_identifier.revision,
        output_file=destination_file,
        input_text=" ".join(input_text),
    )


if __name__ == "__main__":
    main()
