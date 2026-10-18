import unittest
from pathlib import Path


class TestHoldoutV2ExpansionStructure(unittest.TestCase):
    def setUp(self):
        self.root = Path(
            "benchmark/holdout_v2_expansion"
        )

    def test_expansion_directories_exist(self):
        for name in (
            "cases",
            "annotations",
            "runs",
        ):
            with self.subTest(name=name):
                self.assertTrue(
                    (self.root / name).is_dir()
                )

    def test_readme_documents_frozen_boundary(self):
        text = (
            self.root / "README.md"
        ).read_text(encoding="utf-8-sig")

        required = (
            "frozen Holdout v2 baseline",
            (
                "Commit the Ground Truth before "
                "running Why-Blame."
            ),
            (
                "Score the expansion cohort separately "
                "from the frozen Holdout v2 cohort."
            ),
            (
                "Do not derive a reason from the "
                "Ground Truth label."
            ),
            (
                "Do not treat `NOT_OBSERVED` as "
                "evidence that a claim is false."
            ),
            (
                "The frozen Holdout v2 scorer must not "
                "automatically discover expansion cases."
            ),
        )

        for fragment in required:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_expansion_is_outside_frozen_holdout_directory(self):
        frozen = Path(
            "benchmark/holdout_v2"
        ).resolve()
        expansion = self.root.resolve()

        self.assertNotEqual(expansion, frozen)
        self.assertNotIn(
            frozen,
            expansion.parents,
        )

    def test_expansion_starts_without_case_artifacts(self):
        for directory in (
            self.root / "cases",
            self.root / "annotations",
        ):
            json_files = list(
                directory.glob("*.json")
            )

            with self.subTest(directory=directory):
                self.assertEqual(json_files, [])


if __name__ == "__main__":
    unittest.main()
