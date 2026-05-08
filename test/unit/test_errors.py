from contextlib import redirect_stderr
import io
import unittest



import pilo


class TestErrors(unittest.TestCase):

    def test_fatal_error_model(self):
        err = pilo.FatalError("bad things")

        self.assertEqual(str(err), "bad things")

    def test_cli_prints_error_and_exits(self):
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            with self.assertRaises(SystemExit):
                pilo.run_main(
                    lambda: pilo.fatal("boom")
                )

        self.assertEqual(
            stderr.getvalue().strip(),
            "ERROR: boom",
        )
