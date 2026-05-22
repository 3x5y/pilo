import subprocess
import unittest
from unittest.mock import patch, Mock, call

from pathlib import Path

from pilo import zfs
import pilotest


class TestZfsRun(pilotest.TestCase):

    @patch("subprocess.run")
    def test_zfs_run_default_check_true(self, run):
        proc = Mock()
        proc.stdout = ""
        run.return_value = proc

        zfs.run(["zfs", "list"])

        _, kwargs = run.call_args
        self.assertEqual(kwargs["check"], True)

    @patch("subprocess.run")
    def test_zfs_run_capture_text(self, run):
        proc = Mock()
        proc.stdout = ""
        run.return_value = proc

        zfs.run(["zfs", "list"], capture_output=True)

        _, kwargs = run.call_args
        self.assertEqual(kwargs["capture_output"], True)
        self.assertEqual(kwargs["text"], True)

    @patch("subprocess.run")
    def test_dataset_exists_uses_check_false(self, run):
        proc = Mock()
        proc.returncode = 1
        run.return_value = proc

        zfs.dataset_exists("tank/missing")

        _, kwargs = run.call_args
        self.assertEqual(kwargs["check"], False)

    @patch("pilo.zfs.run")
    def test_release(self, run):
        zfs.release("pilo:z1", "tank/a@snap1")

        run.assert_called_once()
        args = run.call_args[0][0]
        self.assertEqual(args, ["zfs", "release", "-r", "pilo:z1", "tank/a@snap1"])

    @patch("pilo.zfs.run")
    def test_destroy_snapshots_empty(self, run):
        zfs.destroy_snapshots([])

        run.assert_not_called()

    @patch("pilo.zfs.run")
    def test_destroy_snapshots_calls_zfs(self, run):
        zfs.destroy_snapshots([
            "pool1/backup@snap1",
            "pool1/backup@snap2",
        ])

        run.assert_called_once()
        args = run.call_args[0][0]
        self.assertEqual(
            args,
            ["zfs", "destroy", "-r", "pool1/backup@snap1,pool1/backup@snap2"],
        )

    @patch("pilo.zfs.run_get_lines")
    def test_list_holds(self, mock_run):
        mock_run.return_value = [
            "tank/a@snap1\tpilo:z1\t1234567890",
            "tank/a@snap2\tpilo:z2\t1234567891",
        ]

        holds = zfs.list_holds("tank/a@snap1")

        self.assertEqual(len(holds), 2)
        self.assertEqual(holds[0], ("tank/a@snap1", "pilo:z1"))
        self.assertEqual(holds[1], ("tank/a@snap2", "pilo:z2"))
        mock_run.assert_called_once_with(
            ["zfs", "holds", "-Hp", "tank/a@snap1"],
            check=False,
        )

    @patch("pilo.zfs.run_get_lines")
    def test_list_holds_empty(self, mock_run):
        mock_run.return_value = []

        holds = zfs.list_holds("tank/a@snap1")

        self.assertEqual(holds, [])

    @patch("pilo.zfs.run_get_lines")
    @patch("pilo.zfs.list_snapshots")
    def test_held_snapshots(self, mock_list, mock_holds):
        mock_list.return_value = [
            "tank/a@snap1",
            "tank/a@snap2",
            "tank/a@snap3",
        ]

        def side_effect(cmd, **kw):
            if cmd[-1] == "tank/a@snap1":
                return [
                    "tank/a@snap1\tpilo:z1\t0"
                ]
            if cmd[-1] == "tank/a@snap2":
                return [
                    "tank/a@snap2\tpilo:z2\t0"
                ]
            return []

        mock_holds.side_effect = side_effect

        held = zfs.held_snapshots("tank/a")

        self.assertEqual(held, ["tank/a@snap1", "tank/a@snap2"])

    @patch("pilo.zfs.run_get_lines")
    @patch("pilo.zfs.list_snapshots")
    def test_held_snapshots_filtered_by_tag(self, mock_list, mock_holds):
        mock_list.return_value = [
            "tank/a@snap1",
            "tank/a@snap2",
        ]

        def side_effect(cmd, **kw):
            if cmd[-1] == "tank/a@snap1":
                return [
                    "tank/a@snap1\tpilo:z1\t0"
                ]
            if cmd[-1] == "tank/a@snap2":
                return [
                    "tank/a@snap2\tpilo:z2\t0"
                ]
            return []

        mock_holds.side_effect = side_effect

        held = zfs.held_snapshots("tank/a", tag="pilo:z1")

        self.assertEqual(held, ["tank/a@snap1"])


class TestSendFullToFile(pilotest.TestCase):

    @patch("subprocess.Popen")
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    def test_creates_parent_dirs_and_sends_full(self, mock_open, mock_mkdir, mock_popen):
        mock_proc = Mock()
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        zfs.send_full_to_file("tank/a@snap1", "/out/streams/test.zfs")

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_open.assert_called_once_with(Path("/out/streams/test.zfs"), "wb")
        mock_popen.assert_called_once_with(
            ["zfs", "send", "-h", "tank/a@snap1"],
            stdout=mock_file,
        )

    @patch("subprocess.Popen")
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    def test_full_failure_raises_fatal(self, mock_open, mock_mkdir, mock_popen):
        mock_proc = Mock()
        mock_proc.wait.return_value = 1
        mock_popen.return_value = mock_proc
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        with self.assert_fatal():
            zfs.send_full_to_file("tank/a@snap1", "/out/streams/test.zfs")


class TestSendIncrementalToFile(pilotest.TestCase):

    @patch("subprocess.Popen")
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    def test_creates_parent_dirs_and_sends_incr(self, mock_open, mock_mkdir, mock_popen):
        mock_proc = Mock()
        mock_proc.wait.return_value = 0
        mock_popen.return_value = mock_proc
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        zfs.send_incremental_to_file("tank/a@base", "tank/a@snap2", "/out/streams/test.zfs")

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_open.assert_called_once_with(Path("/out/streams/test.zfs"), "wb")
        mock_popen.assert_called_once_with(
            ["zfs", "send", "-h", "-I", "tank/a@base", "tank/a@snap2"],
            stdout=mock_file,
        )

    @patch("subprocess.Popen")
    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    def test_incr_failure_raises_fatal(self, mock_open, mock_mkdir, mock_popen):
        mock_proc = Mock()
        mock_proc.wait.return_value = 1
        mock_popen.return_value = mock_proc
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        with self.assert_fatal():
            zfs.send_incremental_to_file("tank/a@base", "tank/a@snap2", "/out/streams/test.zfs")


class TestReplicateFull(pilotest.TestCase):

    @patch("pilo.zfs.simple_pipe")
    @patch("pilo.zfs.set_prop")
    def test_forwards_tee_path(self, mock_set, mock_pipe):
        zfs.replicate_full("tank/a@snap", "tank/b", tee_path="/out/s.zfs")

        mock_pipe.assert_called_once_with(
            ["zfs", "send", "-h", "-R", "tank/a@snap"],
            ["zfs", "receive", "-u", "-o", "readonly=on",
             "-o", "mountpoint=none", "tank/b"],
            tee_path="/out/s.zfs",
        )

    @patch("pilo.zfs.simple_pipe")
    @patch("pilo.zfs.set_prop")
    def test_tee_path_defaults_to_none(self, mock_set, mock_pipe):
        zfs.replicate_full("tank/a@snap", "tank/b")

        mock_pipe.assert_called_once_with(
            ["zfs", "send", "-h", "-R", "tank/a@snap"],
            ["zfs", "receive", "-u", "-o", "readonly=on",
             "-o", "mountpoint=none", "tank/b"],
            tee_path=None,
        )


class TestReplicateIncremental(pilotest.TestCase):

    @patch("pilo.zfs.simple_pipe")
    @patch("pilo.zfs.set_prop")
    def test_forwards_tee_path(self, mock_set, mock_pipe):
        zfs.replicate_incremental(
            "tank/a@base", "tank/a@snap", "tank/b",
            tee_path="/out/s.zfs",
        )

        mock_pipe.assert_called_once_with(
            ["zfs", "send", "-h", "-R", "-I", "tank/a@base",
             "tank/a@snap"],
            ["zfs", "receive", "-u", "-o", "readonly=on",
             "-o", "mountpoint=none", "tank/b"],
            tee_path="/out/s.zfs",
        )

    @patch("pilo.zfs.simple_pipe")
    @patch("pilo.zfs.set_prop")
    def test_tee_path_defaults_to_none(self, mock_set, mock_pipe):
        zfs.replicate_incremental("tank/a@base", "tank/a@snap", "tank/b")

        mock_pipe.assert_called_once_with(
            ["zfs", "send", "-h", "-R", "-I", "tank/a@base",
             "tank/a@snap"],
            ["zfs", "receive", "-u", "-o", "readonly=on",
             "-o", "mountpoint=none", "tank/b"],
            tee_path=None,
        )


class TestSimplePipe(pilotest.TestCase):

    @patch("subprocess.Popen")
    def test_no_tee_creates_two_processes(self, mock_popen):
        src = Mock(stdout=Mock(), wait=Mock(return_value=0))
        sink = Mock(communicate=Mock(return_value=(None, None)),
                    returncode=0)
        mock_popen.side_effect = [src, sink]

        zfs.simple_pipe(["src", "arg"], ["sink", "arg"])

        self.assertEqual(mock_popen.call_count, 2)
        mock_popen.assert_has_calls([
            call(["src", "arg"], stdout=subprocess.PIPE),
            call(["sink", "arg"], stdin=src.stdout),
        ])
        src.stdout.close.assert_called_once()
        sink.communicate.assert_called_once()
        src.wait.assert_called_once()

    @patch("subprocess.Popen")
    def test_no_tee_source_failure_raises_fatal(self, mock_popen):
        src = Mock(stdout=Mock(), wait=Mock(return_value=1))
        sink = Mock(communicate=Mock(return_value=(None, None)),
                    returncode=0)
        mock_popen.side_effect = [src, sink]

        with self.assert_fatal():
            zfs.simple_pipe(["src"], ["sink"])

    @patch("subprocess.Popen")
    def test_no_tee_sink_failure_raises_fatal(self, mock_popen):
        src = Mock(stdout=Mock(), wait=Mock(return_value=0))
        sink = Mock(communicate=Mock(return_value=(None, None)),
                    returncode=1)
        mock_popen.side_effect = [src, sink]

        with self.assert_fatal():
            zfs.simple_pipe(["src"], ["sink"])

    @patch("subprocess.Popen")
    @patch("pathlib.Path.mkdir")
    def test_with_tee_creates_three_processes(self, mock_mkdir, mock_popen):
        src = Mock(stdout=Mock(), wait=Mock(return_value=0))
        tee = Mock(stdout=Mock(), wait=Mock(return_value=0),
                   returncode=0)
        sink = Mock(communicate=Mock(return_value=(None, None)),
                    returncode=0)
        mock_popen.side_effect = [src, tee, sink]

        zfs.simple_pipe(["src"], ["sink"], tee_path="/out/stream.zfs")

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        self.assertEqual(mock_popen.call_count, 3)
        mock_popen.assert_has_calls([
            call(["src"], stdout=subprocess.PIPE),
            call(["tee", "/out/stream.zfs"], stdin=src.stdout,
                 stdout=subprocess.PIPE),
            call(["sink"], stdin=tee.stdout),
        ])
        src.stdout.close.assert_called_once()
        tee.stdout.close.assert_called_once()
        sink.communicate.assert_called_once()
        tee.wait.assert_called_once()
        src.wait.assert_called_once()

    @patch("subprocess.Popen")
    @patch("pathlib.Path.mkdir")
    def test_with_tee_source_failure_raises_fatal(self, mock_mkdir, mock_popen):
        src = Mock(stdout=Mock(), wait=Mock(return_value=1))
        tee = Mock(stdout=Mock(), wait=Mock(return_value=0),
                   returncode=0)
        sink = Mock(communicate=Mock(return_value=(None, None)),
                    returncode=0)
        mock_popen.side_effect = [src, tee, sink]

        with self.assert_fatal():
            zfs.simple_pipe(["src"], ["sink"], tee_path="/out/stream.zfs")

    @patch("subprocess.Popen")
    @patch("pathlib.Path.mkdir")
    def test_with_tee_tee_failure_raises_fatal(self, mock_mkdir, mock_popen):
        src = Mock(stdout=Mock(), wait=Mock(return_value=0))
        tee = Mock(stdout=Mock(), wait=Mock(return_value=1),
                   returncode=1)
        sink = Mock(communicate=Mock(return_value=(None, None)),
                    returncode=0)
        mock_popen.side_effect = [src, tee, sink]

        with self.assert_fatal():
            zfs.simple_pipe(["src"], ["sink"], tee_path="/out/stream.zfs")

    @patch("subprocess.Popen")
    @patch("pathlib.Path.mkdir")
    def test_with_tee_sink_failure_raises_fatal(self, mock_mkdir, mock_popen):
        src = Mock(stdout=Mock(), wait=Mock(return_value=0))
        tee = Mock(stdout=Mock(), wait=Mock(return_value=0),
                   returncode=0)
        sink = Mock(communicate=Mock(return_value=(None, None)),
                    returncode=1)
        mock_popen.side_effect = [src, tee, sink]

        with self.assert_fatal():
            zfs.simple_pipe(["src"], ["sink"], tee_path="/out/stream.zfs")
