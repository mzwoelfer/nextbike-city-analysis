import runpy
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from nextbike_processing import main as main_module


class TestProcessorMain(unittest.TestCase):
    def _run_main(self, arguments):
        return patch.object(sys, "argv", ["processor", *arguments])

    @patch("nextbike_processing.main.process_and_save_trips")
    @patch("nextbike_processing.main.process_and_save_stations")
    def test_dispatches_database_processing_without_export(
        self, mock_process_stations, mock_process_trips
    ):
        with self._run_main(["--city-id", "467", "--date", "2026-06-08"]):
            main_module.main()

        mock_process_stations.assert_called_once_with(
            467, "2026-06-08", None, export_files=False
        )
        mock_process_trips.assert_called_once_with(
            467, "2026-06-08", None, export_files=False
        )

    @patch("nextbike_processing.main.ensure_directory_exists")
    @patch("nextbike_processing.main.process_and_save_trips")
    @patch("nextbike_processing.main.process_and_save_stations")
    def test_export_creates_folder_and_passes_export_arguments(
        self, mock_process_stations, mock_process_trips, mock_ensure_directory
    ):
        arguments = [
            "--city-id", "467", "--date", "2026-06-08",
            "--export-files", "--export-folder", "/tmp/export",
        ]
        with self._run_main(arguments):
            main_module.main()

        mock_ensure_directory.assert_called_once_with("/tmp/export")
        mock_process_stations.assert_called_once_with(
            467, "2026-06-08", "/tmp/export", export_files=True
        )
        mock_process_trips.assert_called_once_with(
            467, "2026-06-08", "/tmp/export", export_files=True
        )

    def test_export_flag_requires_folder(self):
        with self._run_main([
            "--city-id", "467", "--date", "2026-06-08", "--export-files"
        ]):
            with self.assertRaises(SystemExit) as raised:
                main_module.main()

        self.assertEqual(raised.exception.code, 2)

    def test_invalid_date_is_rejected_before_processing(self):
        with self._run_main(["--city-id", "467", "--date", "2026/06/08"]):
            with self.assertRaisesRegex(ValueError, "Invalid date format"):
                main_module.main()

    def test_script_help_entrypoint_exits_without_processing(self):
        output = StringIO()
        with patch.object(sys, "argv", [main_module.__file__, "--help"]):
            with redirect_stdout(output):
                with self.assertRaises(SystemExit) as raised:
                    runpy.run_path(main_module.__file__, run_name="__main__")

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("--city-id", output.getvalue())


if __name__ == "__main__":
    unittest.main()
