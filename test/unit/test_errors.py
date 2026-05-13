from contextlib import redirect_stderr
import io
import unittest

from pilo import error
import pilotest


class TestErrors(pilotest.TestCase):

    def test_fatal_error_model(self):
        err = error.FatalError("bad things")

        self.assertEqual(str(err), "bad things")

    def test_cli_prints_error_and_exits(self):
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            with self.assertRaises(SystemExit):
                error.run_main(
                    lambda: error.fatal("boom")
                )

        self.assertEqual(
            stderr.getvalue().strip(),
            "ERROR: boom",
        )
