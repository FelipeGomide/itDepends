import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from itdepends.analyzer import analyze_repository, TARGET_FILES


# ---------------------------
# Helpers para criar mocks
# ---------------------------

def make_fake_mod(filename, before="OLD", after="NEW"):
    mod = MagicMock()
    mod.new_path = filename
    mod.source_code_before = before
    mod.source_code = after
    return mod


def make_fake_commit(hash_id, author_name, date, modifications):
    commit = MagicMock()
    commit.hash = hash_id
    commit.author.name = author_name
    commit.author_date = date
    commit.modifications = modifications
    return commit


# ---------------------------
# Testes
# ---------------------------

class TestAnalyzer(unittest.TestCase):

    @patch("itdepends.analyzer.Repository")
    def test_analyze_repository_basic(self, mock_repo):
        """Verifica se commits e modificações são coletados corretamente."""

        fake_commit = make_fake_commit(
            "abc123",
            "Alice",
            "2023-01-01",
            [make_fake_mod("pyproject.toml")]
        )

        mock_repo.return_value.traverse_commits.return_value = [fake_commit]

        df = analyze_repository("fake/repo")

        self.assertEquals(len(df), 1)

        row = df.iloc[0]
        self.assertEquals(row["repository"], "fake/repo")
        self.assertEquals(row["commit_hash"], "abc123")
        self.assertEquals(row["author"], "Alice")
        self.assertEquals(row["file"], "pyproject.toml")

    @patch("itdepends.analyzer.Repository")
    def test_ignore_non_target_files(self, mock_repo):
        """Verifica que arquivos fora de TARGET_FILES são ignorados."""

        fake_commit = make_fake_commit(
            "def456",
            "Bob",
            "2023-01-02",
            [make_fake_mod("README.md")]
        )

        mock_repo.return_value.traverse_commits.return_value = [fake_commit]

        df = analyze_repository("fake/repo")

        self.assertTrue(df.empty)
        self.assertEquals(len(df), 0)

    @patch("itdepends.analyzer.Repository")
    def test_multiple_modifications(self, mock_repo):
        """Verifica se múltiplas modificações são coletadas."""

        fake_commit = make_fake_commit(
            "zzz999",
            "Carol",
            "2023-01-03",
            [
                make_fake_mod("pyproject.toml"),
                make_fake_mod("requirements.txt"),
            ]
        )

        mock_repo.return_value.traverse_commits.return_value = [fake_commit]

        df = analyze_repository("fake/repo")

        self.assertEquals(len(df), 2)

        files = set(df["file"])
        for f in TARGET_FILES:
            self.assertIn(f, files)

    @patch("itdepends.analyzer.Repository")
    def test_parsing_error_handling(self, mock_repo):
        """Testa se erros no parsing são capturados corretamente."""

        fake_mod = make_fake_mod("pyproject.toml")

        fake_commit = make_fake_commit(
            "oops111",
            "Dave",
            "2023-01-04",
            [fake_mod]
        )

        mock_repo.return_value.traverse_commits.return_value = [fake_commit]

        with patch("itdepends.analyzer.parse_dependency_file", side_effect=Exception("Erro")):
            df = analyze_repository("fake/repo")

        row = df.iloc[0]

        self.assertIsNone(row["parsed_before"])
        self.assertIsNone(row["parsed_after"])


if __name__ == "__main__":
    unittest.main()
