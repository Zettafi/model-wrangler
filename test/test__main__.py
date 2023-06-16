import unittest
from pathlib import Path
from unittest.mock import patch, ANY

from click.testing import CliRunner
from wrangler.__main__ import main
from wrangler.model_handlers import TextTransformModelHandler, ImageGenerateModelHandler
from wrangler.request_handlers import (
    TextTransformRequestHandler,
    ImageGenerateRequestHandler,
)


class CLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._runner = CliRunner()
        patcher = patch("wrangler.__main__.cli_serve")
        self._serve_patch = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("wrangler.__main__.cli_run")
        self._run_patch = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("wrangler.__main__.cli_run_image")
        self._run_image_patch = patcher.start()
        self.addCleanup(patcher.stop)

    def test_main_is_group(self):
        result = self._runner.invoke(main)
        self.assertEqual(0, result.exit_code)
        self.assertRegex(result.output, "Usage: wrangler")

    def test_main_serve_is_group(self):
        result = self._runner.invoke(main, ["serve"])
        self.assertEqual(0, result.exit_code)
        self.assertRegex(result.output, "Usage: wrangler serve")

    def test_main_serve_text_transform_is_command_requiring_arguments(self):
        result = self._runner.invoke(main, ["serve", "text-transform"])
        self.assertNotEqual(0, result.exit_code)
        self.assertRegex(result.output, "Usage: wrangler serve text-transform")

    def test_main_serve_text_transform_defaults_as_expected(self):
        result = self._runner.invoke(main, ["serve", "text-transform", "model"])
        self.assertEqual(0, result.exit_code, result.output)
        self._serve_patch.assert_called_once_with(
            service_name="Text Transform Model Service",
            model_handler_class=TextTransformModelHandler,
            model_identifier=ANY,
            model_revision=ANY,
            model_offload_folder=None,
            request_handler_class=TextTransformRequestHandler,
            webserver_bind="127.0.0.1:8000",
            webserver_access_log="-",
            webserver_error_log="-",
        )

    def test_main_serve_text_transform_splits_model_identifier_and_revision(self):
        result = self._runner.invoke(main, ["serve", "text-transform", "model:revision"])
        self.assertEqual(0, result.exit_code, result.output)
        self._serve_patch.assert_called_once_with(
            service_name=ANY,
            model_handler_class=ANY,
            model_identifier="model",
            model_revision="revision",
            model_offload_folder=ANY,
            request_handler_class=ANY,
            webserver_bind=ANY,
            webserver_access_log=ANY,
            webserver_error_log=ANY,
        )

    def test_main_serve_text_transform_defaults_model_revision_to_none(self):
        result = self._runner.invoke(main, ["serve", "text-transform", "model"])
        self.assertEqual(0, result.exit_code, result.output)
        self._serve_patch.assert_called_once_with(
            service_name=ANY,
            model_handler_class=ANY,
            model_identifier="model",
            model_revision=None,
            model_offload_folder=ANY,
            request_handler_class=ANY,
            webserver_bind=ANY,
            webserver_access_log=ANY,
            webserver_error_log=ANY,
        )

    def test_main_serve_text_transform_passes_options(self):
        result = self._runner.invoke(
            main,
            [
                "serve",
                "--service-name",
                "service_name",
                "--bind",
                "bind",
                "--access-log",
                "access_log",
                "--error-log",
                "error_log",
                "text-transform",
                "--model-offload-folder",
                "model_offload_folder",
                "model",
            ],
        )
        self.assertEqual(0, result.exit_code, result.output)
        self._serve_patch.assert_called_once_with(
            service_name="service_name",
            model_handler_class=ANY,
            model_identifier=ANY,
            model_revision=ANY,
            model_offload_folder=Path("model_offload_folder"),
            request_handler_class=ANY,
            webserver_bind="bind",
            webserver_access_log="access_log",
            webserver_error_log="error_log",
        )

    def test_main_serve_image_generate_is_command_requiring_arguments(self):
        result = self._runner.invoke(main, ["serve", "image-generate"])
        self.assertNotEqual(0, result.exit_code)
        self.assertRegex(result.output, "Usage: wrangler serve image-generate")

    def test_main_serve_image_generate_defaults_as_expected(self):
        result = self._runner.invoke(main, ["serve", "image-generate", "model"])
        self.assertEqual(0, result.exit_code, result.output)
        self._serve_patch.assert_called_once_with(
            service_name="Image Generation Model Service",
            model_handler_class=ImageGenerateModelHandler,
            model_identifier=ANY,
            model_revision=ANY,
            model_offload_folder=None,
            request_handler_class=ImageGenerateRequestHandler,
            webserver_bind="127.0.0.1:8000",
            webserver_access_log="-",
            webserver_error_log="-",
        )

    def test_main_serve_image_generate_splits_model_identifier_and_revision(self):
        result = self._runner.invoke(main, ["serve", "image-generate", "model:revision"])
        self.assertEqual(0, result.exit_code, result.output)
        self._serve_patch.assert_called_once_with(
            service_name=ANY,
            model_handler_class=ANY,
            model_identifier="model",
            model_revision="revision",
            model_offload_folder=None,
            request_handler_class=ANY,
            webserver_bind=ANY,
            webserver_access_log=ANY,
            webserver_error_log=ANY,
        )

    def test_main_serve_image_generate_defaults_model_revision_to_none(self):
        result = self._runner.invoke(main, ["serve", "image-generate", "model"])
        self.assertEqual(0, result.exit_code, result.output)
        self._serve_patch.assert_called_once_with(
            service_name=ANY,
            model_handler_class=ANY,
            model_identifier="model",
            model_revision=None,
            model_offload_folder=ANY,
            request_handler_class=ANY,
            webserver_bind=ANY,
            webserver_access_log=ANY,
            webserver_error_log=ANY,
        )

    def test_main_serve_image_generate_passes_options(self):
        result = self._runner.invoke(
            main,
            [
                "serve",
                "--service-name",
                "service_name",
                "--bind",
                "bind",
                "--access-log",
                "access_log",
                "--error-log",
                "error_log",
                "image-generate",
                "model",
            ],
        )
        self.assertEqual(0, result.exit_code, result.output)
        self._serve_patch.assert_called_once_with(
            service_name="service_name",
            model_handler_class=ANY,
            model_identifier=ANY,
            model_revision=ANY,
            model_offload_folder=ANY,
            request_handler_class=ANY,
            webserver_bind="bind",
            webserver_access_log="access_log",
            webserver_error_log="error_log",
        )

    def test_main_run_is_group(self):
        result = self._runner.invoke(main, ["run"])
        self.assertEqual(0, result.exit_code)
        self.assertRegex(result.output, "Usage: wrangler run")

    def test_main_run_text_transform_is_command_requiring_arguments(self):
        result = self._runner.invoke(main, ["run", "text-transform"])
        self.assertNotEqual(0, result.exit_code)
        self.assertRegex(result.output, "Usage: wrangler run text-transform")

    def test_main_run_text_transform_defaults_as_expected(self):
        result = self._runner.invoke(
            main,
            ["run", "text-transform", "model", "Input"],
        )
        self.assertEqual(0, result.exit_code, result.output)
        self._run_patch.assert_called_once_with(
            model_handler_class=TextTransformModelHandler,
            model_identifier=ANY,
            model_revision=ANY,
            model_offload_folder=None,
            input_text=ANY,
        )

    def test_main_run_text_transform_passes_options_and_arguments(self):
        result = self._runner.invoke(
            main,
            [
                "run",
                "text-transform",
                "--model-offload-folder",
                "model_offload_folder",
                "model:revision",
                "input",
            ],
        )
        self.assertEqual(0, result.exit_code, result.output)
        self._run_patch.assert_called_once_with(
            model_handler_class=ANY,
            model_identifier="model",
            model_revision="revision",
            model_offload_folder=Path("model_offload_folder"),
            input_text="input",
        )

    def test_main_run_image_generate_is_command_requiring_arguments(self):
        result = self._runner.invoke(main, ["run", "image-generate"])
        self.assertNotEqual(0, result.exit_code)
        self.assertRegex(result.output, "Usage: wrangler run image")

    def test_main_run_image_generate_defaults_as_expected(self):
        result = self._runner.invoke(
            main,
            ["run", "image-generate", "model", "output_path", "Input"],
        )
        self.assertEqual(0, result.exit_code, result.output)
        self._run_image_patch.assert_called_once_with(
            model_handler_class=ImageGenerateModelHandler,
            model_identifier=ANY,
            model_revision=ANY,
            output_file=ANY,
            input_text=ANY,
        )

    def test_main_run_image_generate_passes_options_and_arguments(self):
        result = self._runner.invoke(
            main,
            [
                "run",
                "image-generate",
                "model:revision",
                "destination_file",
                "lot's",
                "of",
                "input",
                "to",
                "see",
                "here",
            ],
        )
        self.assertEqual(0, result.exit_code, result.output)
        self._run_image_patch.assert_called_once_with(
            model_handler_class=ANY,
            model_identifier="model",
            model_revision="revision",
            output_file=Path("destination_file"),
            input_text="lot's of input to see here",
        )


if __name__ == "__main__":
    unittest.main()
