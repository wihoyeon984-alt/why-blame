import io
import unittest
from unittest.mock import patch

import main


class MainCliTests(unittest.TestCase):
    def run_main(self, arguments):
        output = io.StringIO()

        argv_patch = patch.object(
            main.sys,
            "argv",
            ["why-blame"] + arguments,
        )
        stdout_patch = patch(
            "sys.stdout",
            output,
        )

        with argv_patch:
            with stdout_patch:
                main.main()

        return output.getvalue()

    def test_long_version_option(self):
        version_patch = patch.object(
            main,
            "get_version",
            return_value="1.2.3",
        )

        with version_patch:
            output = self.run_main(
                ["--version"]
            )

        self.assertEqual(
            output,
            "why-blame 1.2.3\n",
        )

    def test_short_version_option(self):
        version_patch = patch.object(
            main,
            "get_version",
            return_value="1.2.3",
        )

        with version_patch:
            output = self.run_main(["-V"])

        self.assertEqual(
            output,
            "why-blame 1.2.3\n",
        )

    def test_get_version_uses_local_pyproject(self):
        pyproject_text = (
            '[project]\n'
            'name = "why-blame"\n'
            'version = "9.8.7"\n'
        )

        file_patch = patch.object(
            main.Path,
            "is_file",
            return_value=True,
        )
        read_patch = patch.object(
            main.Path,
            "read_text",
            return_value=pyproject_text,
        )
        metadata_patch = patch.object(
            main,
            "version",
        )

        with file_patch:
            with read_patch:
                with metadata_patch as mocked_version:
                    result = main.get_version()

        self.assertEqual(result, "9.8.7")
        mocked_version.assert_not_called()

    def test_get_version_uses_package_metadata(self):
        file_patch = patch.object(
            main.Path,
            "is_file",
            return_value=False,
        )
        metadata_patch = patch.object(
            main,
            "version",
            return_value="0.3.4",
        )

        with file_patch:
            with metadata_patch as mocked_version:
                result = main.get_version()

        self.assertEqual(result, "0.3.4")
        mocked_version.assert_called_once_with(
            "why-blame"
        )

    def test_get_version_falls_back_when_not_installed(self):
        file_patch = patch.object(
            main.Path,
            "is_file",
            return_value=False,
        )
        metadata_patch = patch.object(
            main,
            "version",
            side_effect=main.PackageNotFoundError,
        )

        with file_patch:
            with metadata_patch:
                result = main.get_version()

        self.assertEqual(result, "unknown")


if __name__ == "__main__":
    unittest.main()