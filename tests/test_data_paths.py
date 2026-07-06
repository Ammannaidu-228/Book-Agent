import os

from src.main import resolve_data_file_path


def test_resolve_data_file_path_finds_repo_csv():
    path = resolve_data_file_path("books_with_emotions.csv")
    assert path is not None
    assert os.path.basename(path) == "books_with_emotions.csv"
    assert os.path.exists(path)
