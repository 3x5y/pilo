import subprocess
import unittest
from unittest.mock import patch

from pilo import state
from pilo import status
import pilotest


class TestSystemStatusModel(pilotest.TestCase):

    def test_empty_status_is_ok(self):
        report = state.ValidationReport()
        self.assertTrue(report.is_healthy)
        self.assertEqual(report.issues, [])

    @patch("pilo.git.is_dirty", return_value=True)
    def test_dirty_repo(self, _):
        cx = pilotest.make_context()
        report = state.ValidationReport()

        with pilotest.make_tmp_context() as cx:
            (cx.admin_path / "repo" / ".git").mkdir(parents=True, exist_ok=True)
            report.extend(status.collect_transient_validation(cx))

        self.assertFalse(report.is_healthy)
        issues = report.by_component("transient")
        self.assertEqual(len(issues), 1)
        self.assertIn('uncommitted', issues[0].message)

    @patch("pilo.state.collect_validation_report")
    @patch("pilo.status.collect_transient_validation")
    def test_collect_system_status_uses_validation_report(self,
        transient,
        collect,
    ):
        collect.return_value = state.ValidationReport()

        cx = pilotest.make_context()

        report = status.collect_report(cx)

        self.assertIsInstance(report, state.ValidationReport)
        inc = {"datasets", "snapshot", "replication"}
        collect.assert_called_once_with(cx, include=inc)
        transient.assert_called_once()

    def test_render_validation_issue(self):
        i = state.ValidationIssue(
            code="foo.bar",
            message="bad stuff",
            severity=state.ValidationSeverity.WARN,
            component="foo",
        )

        rendered = status.render_validation_issue(i)

        self.assertEqual(rendered, "WARN: foo.bar: bad stuff")

    def test_manifest_status_missing_manifest_is_ok(self):
        cx = pilotest.make_context()
        report = state.ValidationReport()

        report.extend(status.collect_manifest_validation(cx))

        self.assertTrue(report.is_healthy)

    @patch("subprocess.run")
    def test_manifest_status_ok(self, mock_run):
        with pilotest.make_tmp_context() as cx:
            report = state.ValidationReport()
            manifest = cx.admin_path / "manifest" / "pile.manifest"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text("abc\n")

            report.extend(status.collect_manifest_validation(cx))

            self.assertTrue(report.is_healthy)
            issues = report.by_component("manifest")
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].message, "pile verified")

    @patch("subprocess.run")
    def test_manifest_status_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            1,
            ["sha256sum"],
        )

        with pilotest.make_tmp_context() as cx:
            report = state.ValidationReport()

            manifest = cx.admin_path / "manifest" / "pile.manifest"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text("abc\n")

            report.extend(status.collect_manifest_validation(cx))

            self.assertFalse(report.is_healthy)

            issues = report.by_component("manifest")
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].message, "pile verification failed")

    @patch("pilo.state.collect_validation_report")
    @patch("pilo.status.check_manifest")
    def test_collect_calls_manifest(self, mock_manifest, *_):
        cx = pilotest.make_context()

        status.collect_report(cx)

        mock_manifest.assert_any_call(cx, "pile")
        mock_manifest.assert_any_call(cx, "collection")
        mock_manifest.assert_any_call(cx, "filing")

    @patch("pilo.state.collect_validation_report")
    @patch("pilo.status.check_manifest")
    def test_collect_manifest_only(self, mock_manifest, *_):
        cx = pilotest.make_context()

        status.collect_report(cx, check="manifest")

        self.assertEqual(mock_manifest.call_count, 3)
