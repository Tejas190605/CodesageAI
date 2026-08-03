import pytest
from app.utils.diff_utils import is_reviewable_file, format_and_truncate_diff


def test_is_reviewable_file_accepts_source_files():
    """Tests that standard source files, documentation, and Dockerfiles are accepted."""
    accepted_files = [
        "app/main.py",
        "src/index.ts",
        "src/App.tsx",
        "src/main.jsx",
        "backend/server.js",
        "src/service.go",
        "src/lib.rs",
        "src/Main.java",
        "src/program.cpp",
        "README.md",
        "Dockerfile",
    ]
    for filepath in accepted_files:
        assert is_reviewable_file(filepath) is True, f"Failed to accept valid file: {filepath}"


def test_is_reviewable_file_rejects_non_reviewable():
    """Tests that images, binaries, minified assets, lockfiles, and vendor directories are rejected."""
    rejected_files = [
        "app/__pycache__/main.pyc",
        "image.png",
        "photo.jpeg",
        "document.pdf",
        "archive.zip",
        "dist/app.min.js",
        "styles/site.min.css",
        "node_modules/pkg/index.js",
        "vendor/library/file.php",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
    ]
    for filepath in rejected_files:
        assert is_reviewable_file(filepath) is False, f"Failed to reject non-reviewable file: {filepath}"


def test_is_reviewable_file_handles_windows_paths():
    """Tests that Windows-style backslash paths are handled correctly."""
    assert is_reviewable_file(r"dist\app.min.js") is False
    assert is_reviewable_file(r"app\__pycache__\x.pyc") is False
    assert is_reviewable_file(r"app\services\ai_review.py") is True


def test_small_patch_unchanged():
    """Tests that patches under the limit remain intact."""
    files = [{"filename": "main.py", "status": "modified", "patch": "def foo(): pass"}]
    formatted, count = format_and_truncate_diff(files, max_patch_chars_per_file=1000, max_total_diff_chars=5000)
    assert count == 1
    assert "def foo(): pass" in formatted
    assert "[PATCH TRUNCATED]" not in formatted


def test_per_file_patch_truncation():
    """Tests that an individual large patch is truncated with a marker."""
    large_patch = "A" * 5000
    files = [{"filename": "large.py", "status": "modified", "patch": large_patch}]
    formatted, count = format_and_truncate_diff(files, max_patch_chars_per_file=1000, max_total_diff_chars=5000)
    assert count == 1
    assert "[PATCH TRUNCATED]" in formatted
    assert len(formatted) < 5000


def test_total_diff_budget_truncation():
    """Tests that overall diff budget limit triggers overall truncation marker."""
    files = [
        {"filename": f"file_{i}.py", "status": "modified", "patch": "X" * 1000}
        for i in range(10)
    ]
    formatted, count = format_and_truncate_diff(files, max_patch_chars_per_file=2000, max_total_diff_chars=2500)
    assert count >= 1
    assert "[DIFF TRUNCATED - OVERALL LIMIT REACHED]" in formatted


def test_empty_and_missing_patch_handling():
    """Tests that empty or missing file lists/patches are handled safely."""
    assert format_and_truncate_diff([]) == ("", 0)

    files = [
        {"filename": "binary.png", "status": "added", "patch": None},
        {"filename": "empty.py", "status": "modified", "patch": ""},
        {"filename": "nopatch.py", "status": "modified", "patch": "No patch available"},
    ]
    formatted, count = format_and_truncate_diff(files)
    assert count == 0
    assert formatted == ""


def test_unicode_truncation_safety():
    """Tests that patch truncation does not corrupt multi-byte Unicode strings."""
    unicode_patch = "🚀 CodeSage AI Review 🎉" * 200
    files = [{"filename": "unicode.py", "status": "modified", "patch": unicode_patch}]
    formatted, count = format_and_truncate_diff(files, max_patch_chars_per_file=100)
    assert count == 1
    assert "[PATCH TRUNCATED]" in formatted
    # String operations must complete without raising UnicodeDecodeError / UnicodeEncodeError
    assert isinstance(formatted, str)
