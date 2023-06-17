import base64
import os.path
import pathlib
import subprocess
import sys
import time
import unittest
from io import BytesIO
from tempfile import TemporaryDirectory, NamedTemporaryFile
from unittest.mock import ANY

import httpx
from PIL import Image
from click.testing import CliRunner

from wrangler.__main__ import main

IMAGE_GENERATE_TEST_MODEL = str(
    pathlib.Path(__file__).parent.joinpath("assets/hf-internal-testing_unidiffuser-test-v1")
)

TEXT_TRANSFORM_TEST_MODEL = str(
    pathlib.Path(__file__).parent.joinpath("assets/hf-internal-testing_tiny-random-gpt2")
)


class CliRunTextCompleteIntegrationTestCase(unittest.TestCase):
    """Tests from the CLI serve entrypoint to the model handler"""

    def test_returns_decoded_model_generate_results(self):
        model = str(
            pathlib.Path(__file__).parent.joinpath("assets/hf-internal-testing_tiny-random-gpt2")
        )

        with TemporaryDirectory() as temp_folder:
            runner = CliRunner()
            response = runner.invoke(
                main,
                [
                    "run",
                    "text-transform",
                    "--model-offload-folder",
                    temp_folder,
                    model,
                    "Stuff",
                ],
                env={
                    "TOKENIZERS_PARALLELISM": "false",
                },
            )
        if response.exception:
            raise response.exception
        self.assertEqual(0, response.exit_code, response.output)
        actual = response.output
        self.assertIn("Stuff set set set set setylganibibibibibibibibib\n", actual)


class CliRunImageGenerateIntegrationTestCase(unittest.TestCase):
    """Tests from the CLI serve entrypoint to the model handler"""

    def test_writes_image_file_as_expected(self):
        temp_file = NamedTemporaryFile(suffix=".png")
        with temp_file as fp:
            runner = CliRunner()
            response = runner.invoke(
                main,
                [
                    "run",
                    "image-generate",
                    IMAGE_GENERATE_TEST_MODEL,
                    temp_file.name,
                    "Stuff",
                ],
            )
            if response.exception:
                raise response.exception
            self.assertEqual(0, response.exit_code, response.output)
            image = Image.open(fp)
            image.verify()
            self.assertEqual("PNG", image.format)


class ServerManager:
    def start_server(self, socket_filename, run_args):
        args = [
            sys.executable,
            "-m",
            "wrangler",
            "serve",
            "--bind",
            f"unix:{socket_filename}",
            "--access-log",
            "-",
            "--error-log",
            "-",
        ]
        args.extend(run_args)
        self._server_process = subprocess.Popen(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        start = time.perf_counter()
        while not os.path.isfile(socket_filename) and time.perf_counter() - start < 5.0:
            time.sleep(0.001)

    def stop_server(self):
        if self._server_process:
            self._server_process.kill()
            start = time.perf_counter()
            while self._server_process.poll() and time.perf_counter() - start < 5.0:
                time.sleep(0.001)


class CliServeTextTransformIntegrationTestCase(unittest.TestCase, ServerManager):
    """Tests from the CLI serve entrypoint to the model handler"""

    def setUp(self):
        td = TemporaryDirectory()
        temp_directory = td.__enter__()
        self.addCleanup(td.__exit__, None, None, None)
        socket_file = NamedTemporaryFile(suffix=".sock")
        with socket_file:  # Identify a proper temporary file for the file system
            socket_filename = socket_file.name
        command_arge = [
            "text-transform",
            "--model-offload-folder",
            temp_directory,
            TEXT_TRANSFORM_TEST_MODEL,
        ]
        self.start_server(socket_filename, command_arge)

        transport = httpx.HTTPTransport(uds=socket_filename)
        self._client = httpx.Client(transport=transport)

    def tearDown(self) -> None:
        self.stop_server()

    def test_ping_returns(self):
        response = self._client.get("http://socket/ping")
        response.raise_for_status()
        self.assertEqual(204, response.status_code)

    def test_docs_webpage_exists(self):
        response = self._client.get("http://socket/docs")
        response.raise_for_status()
        self.assertRegex(response.headers.get("content-type"), r"^text/html")

    def test_submit_request_returns_expected_result(self):
        expected = {"generated_text": "Input Texttttazazazazazazazazaz"}
        response = self._client.post("http://socket/", json={"input": "Input Text"})
        response.raise_for_status()
        self.assertEqual(expected, response.json())


class CliServeImageGenerateIntegrationTestCase(unittest.TestCase, ServerManager):
    """Tests from the CLI serve entrypoint to the model handler"""

    def setUp(self):
        socket_file = NamedTemporaryFile(suffix=".sock")
        with socket_file:  # Identify a proper temporary file for the file system
            socket_filename = socket_file.name
        command_args = [
            "image-generate",
            IMAGE_GENERATE_TEST_MODEL,
        ]
        self.start_server(socket_filename, command_args)

        transport = httpx.HTTPTransport(uds=socket_filename)
        self._client = httpx.Client(transport=transport)

    def tearDown(self) -> None:
        self.stop_server()

    def test_ping_returns(self):
        response = self._client.get("http://socket/ping")
        response.raise_for_status()
        self.assertEqual(204, response.status_code)

    def test_docs_webpage_exists(self):
        response = self._client.get("http://socket/docs")
        response.raise_for_status()
        self.assertRegex(response.headers.get("content-type"), r"^text/html")

    def test_submit_request_returns_expected_result(self):
        expected = {"image": ANY, "format": "PNG"}
        response = self._client.post("http://socket/", json={"input": "Input Text"})
        response.raise_for_status()
        actual = response.json()
        self.assertEqual(expected, actual)
        image_bytes = base64.b64decode(actual["image"])
        bytesio = BytesIO(image_bytes)
        image = Image.open(bytesio)
        image.verify()


if __name__ == "__main__":
    unittest.main()
