from pathlib import Path
from unittest.mock import patch

from pilo.back.snapshot import SnapshotName, SnapshotKind
import pilotest


class TestStreamExportCmd(pilotest.TestCase):

    @patch("sys.argv", ["pilo-stream-export"])
    def test_no_args_exits(self):
        mod = pilotest.import_command("stream-export")
        with pilotest.suppress_stderr():
            with self.assertRaises(SystemExit):
                mod.main()

    @patch("sys.argv", ["pilo-stream-export", "tank/a"])
    def test_missing_at_fatal(self):
        mod = pilotest.import_command("stream-export")
        with self.assert_fatal():
            mod.main()

    @patch("sys.argv", ["pilo-stream-export", "tank/a@r-20260522"])
    def test_non_canonical_snapshot_fatal(self):
        mod = pilotest.import_command("stream-export")
        with self.assert_fatal():
            mod.main()

    @patch("pilo.back.streams.export_incremental_stream")
    @patch("sys.argv", [
        "pilo-stream-export",
        "tank/a@20260522_000000_000000-mark",
    ])
    def test_full_export(self, mock_export):
        mock_export.return_value = Path("/out/streams/20260522/test.zfs")
        mod = pilotest.import_command("stream-export")
        with pilotest.suppress_stdout():
            mod.main()

        mock_export.assert_called_once()
        args, kwargs = mock_export.call_args
        self.assertEqual(args[0], "tank/a")
        self.assertEqual(args[1].format(),
                         "20260522_000000_000000-mark")
        self.assertIsNone(kwargs.get("base"))

    @patch("pilo.back.streams.export_incremental_stream")
    @patch("sys.argv", [
        "pilo-stream-export",
        "tank/a@20260522_000002_000000-reg",
        "tank/a@20260522_000000_000000-mark",
    ])
    def test_incremental_export(self, mock_export):
        mock_export.return_value = Path("/out/streams/20260522/test.zfs")
        mod = pilotest.import_command("stream-export")
        with pilotest.suppress_stdout():
            mod.main()

        mock_export.assert_called_once()
        args, kwargs = mock_export.call_args
        self.assertEqual(args[0], "tank/a")
        self.assertEqual(args[1].format(),
                         "20260522_000002_000000-reg")
        self.assertIsNotNone(kwargs.get("base"))
        self.assertEqual(kwargs["base"].format(),
                         "20260522_000000_000000-mark")

    @patch("pilo.back.streams.export_incremental_stream")
    @patch("sys.argv", [
        "pilo-stream-export",
        "tank/a@20260522_000000_000000-mark",
    ])
    def test_prints_filepath(self, mock_export):
        mock_export.return_value = Path("/out/streams/20260522/test.zfs")
        mod = pilotest.import_command("stream-export")
        with patch("builtins.print") as mock_print:
            mod.main()
        mock_print.assert_called_once_with(
            Path("/out/streams/20260522/test.zfs"))

    @patch("sys.argv", [
        "pilo-stream-export",
        "tank/a@20260522_000000_000000-reg",
        "tank/a@non-canonical",
    ])
    def test_non_canonical_base_fatal(self):
        mod = pilotest.import_command("stream-export")
        with self.assert_fatal():
            mod.main()
