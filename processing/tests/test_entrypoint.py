import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestScheduledProcessing(unittest.TestCase):
    def test_normal_schedule_uses_date_after_midnight_wait(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            bin_path = temporary_path / "bin"
            bin_path.mkdir()
            marker_path = temporary_path / "after_midnight"
            processor_args_path = temporary_path / "processor_args"

            commands = {
                "date": """#!/bin/sh
case "$*" in
  "-d tomorrow 00:00 +%s") printf '200\\n' ;;
  "+%s") printf '100\\n' ;;
  "-d yesterday +%Y-%m-%d")
    if [ -f "$SIMULATED_AFTER_MIDNIGHT" ]; then
      printf '2026-09-30\\n'
    else
      printf '2026-09-29\\n'
    fi
    ;;
  *) exit 1 ;;
esac
""",
                "sleep": """#!/bin/sh
touch "$SIMULATED_AFTER_MIDNIGHT"
""",
                "python": """#!/bin/sh
printf '%s\\n' "$*" > "$PROCESSOR_ARGS_FILE"
exit 42
""",
            }
            for command_name, command_content in commands.items():
                command_path = bin_path / command_name
                command_path.write_text(command_content, encoding="utf-8")
                command_path.chmod(0o755)

            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{bin_path}{os.pathsep}{environment['PATH']}",
                    "CITY_IDS": "467",
                    "TEST_RUN_SECONDS": "",
                    "SIMULATED_AFTER_MIDNIGHT": str(marker_path),
                    "PROCESSOR_ARGS_FILE": str(processor_args_path),
                }
            )
            entrypoint_path = Path(__file__).resolve().parents[1] / "entrypoint.sh"
            result = subprocess.run(
                ["/bin/bash", str(entrypoint_path)],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 42, result.stdout + result.stderr)
            self.assertIn("--date 2026-09-30", processor_args_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
