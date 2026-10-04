import sys
import subprocess
import unittest

from nextbike_processing import main as main_module


class TestProcessorMain(unittest.TestCase):
    def test_export_flag_requires_folder(self):
        with self.assertRaises(SystemExit) as raised:
            main_module.main([
                "--city-id", "467", "--date", "2026-06-08", "--export-files"
            ])

        self.assertEqual(raised.exception.code, 2)

    def test_invalid_date_is_rejected_before_processing(self):
        with self.assertRaisesRegex(ValueError, "Invalid date format"):
            main_module.main(["--city-id", "467", "--date", "2026/06/08"])

    def test_script_help_entrypoint_exits_without_processing(self):
        result = subprocess.run(
            [sys.executable, "-m", "nextbike_processing.main", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--city-id", result.stdout)


if __name__ == "__main__":
    unittest.main()
