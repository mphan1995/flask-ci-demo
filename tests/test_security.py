from functions.security import validate_path


def test_validate_path_allows_within_root(tmp_path):
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    target = allowed_root / "file.txt"
    ok, error = validate_path(str(target), [str(allowed_root)], safe_mode=False)
    assert ok
    assert error == ""


def test_validate_path_blocks_outside_root(tmp_path):
    allowed_root = tmp_path / "allowed"
    allowed_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "file.txt"
    ok, error = validate_path(str(target), [str(allowed_root)], safe_mode=False)
    assert not ok
    assert error == "path_not_allowed"
