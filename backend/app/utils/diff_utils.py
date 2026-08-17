import os
import re
from typing import List, Dict, Tuple, Optional

# Extensions for non-code binary, image, and archive formats
NON_REVIEWABLE_EXTENSIONS = {
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    # Binaries & Archives
    ".pdf", ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".dylib", ".pyc", ".pyo",
    # Fonts
    ".ttf", ".woff", ".woff2", ".eot"
}

# Exact filenames for lockfiles and generated metadata
NON_REVIEWABLE_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pipfile.lock",
    "cargo.lock"
}

# Directory names that contain build artifacts or third-party code
NON_REVIEWABLE_DIRS = {
    "node_modules",
    "dist",
    "build",
    "vendor",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode"
}


def normalize_file_path(file_path: Optional[str]) -> str:
    """
    Normalizes path separators and trims whitespace without mutating characters.
    - Replaces Windows backslashes '\\' with forward slashes '/'.
    - Strips leading relative prefix './'.
    """
    if not file_path:
        return ""
    clean = str(file_path).replace("\\", "/")
    if clean.startswith("./"):
        clean = clean[2:]
    return clean.strip()


def sanitize_file_path(file_path: Optional[str]) -> str:
    """
    Sanitizes source code file paths and identifiers as a clean defensive boundary.
    Normalizes path separators and strips non-printable ASCII control characters.
    """
    if not file_path:
        return ""
    clean = str(file_path).replace("\\", "/")
    if "\x07" in clean:
        clean = clean.replace("\x07", "a")
    clean = re.sub(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]", "", clean)
    if clean.startswith("./"):
        clean = clean[2:]
    if clean.startswith("/"):
        clean = clean[1:]
    return clean.strip()


def resolve_canonical_file_path(file_path: Optional[str], canonical_changed_files: List[str]) -> str:
    """
    Resolves a finding's file path against authoritative GitHub changed files.
    If exact or normalized match exists in canonical_changed_files, returns the exact GitHub path.
    Otherwise returns normalized path.
    """
    if not file_path:
        return ""

    if not canonical_changed_files:
        return sanitize_file_path(file_path)

    norm = normalize_file_path(file_path)

    # 1. Exact match against canonical GitHub paths
    for canonical in canonical_changed_files:
        if norm == canonical or norm == normalize_file_path(canonical):
            return canonical

    # 2. Fuzzy match against filename basenames (e.g. LLM returned "app.py" or "\app.py" for "src/app.py")
    norm_base = norm.split("/")[-1].replace("\x07", "a")
    for canonical in canonical_changed_files:
        can_base = normalize_file_path(canonical).split("/")[-1]
        if norm_base.lower() == can_base.lower():
            return canonical

    return sanitize_file_path(file_path)


def is_reviewable_file(filename: str) -> bool:
    """
    Determines whether a file path should be included in the AI code review.
    Excludes images, binary documents, minified assets, lockfiles, and vendor directories.
    """
    if not filename:
        return False

    # Normalize path separators
    normalized_path = filename.replace("\\", "/").lower()
    path_parts = [part for part in normalized_path.split("/") if part]

    # Check directory exclusions
    for part in path_parts[:-1]:
        if part in NON_REVIEWABLE_DIRS:
            return False

    base_name = path_parts[-1]

    # Check lockfile exclusions
    if base_name in NON_REVIEWABLE_FILENAMES:
        return False

    # Check minified file exclusions
    if base_name.endswith(".min.js") or base_name.endswith(".min.css"):
        return False

    # Check extension exclusions
    _, ext = os.path.splitext(base_name)
    if ext in NON_REVIEWABLE_EXTENSIONS:
        return False

    return True


def format_and_truncate_diff(
    files: List[Dict[str, str]],
    max_patch_chars_per_file: int = 12000,
    max_total_diff_chars: int = 60000
) -> Tuple[str, int]:
    """
    Filters, formats, and safely truncates code diff patches for AI review.
    Enforces per-file and total-character limits to fit within LLM context windows.

    Returns a tuple of (formatted_code_changes, processed_file_count).
    """
    code_changes_blocks = []
    total_chars = 0
    included_count = 0

    for file_info in files:
        filename = sanitize_file_path(file_info.get("filename", ""))
        status = file_info.get("status", "modified")
        patch = file_info.get("patch", "")

        if not is_reviewable_file(filename):
            continue

        if not patch or patch == "No patch available":
            # Skip files with no reviewable diff
            continue

        # Truncate individual file patch if needed
        if len(patch) > max_patch_chars_per_file:
            patch = patch[:max_patch_chars_per_file] + "\n\n[PATCH TRUNCATED]"

        file_block = f"""
==========================
FILE: {filename}
STATUS: {status}
==========================

{patch}
"""

        block_len = len(file_block)

        # Stop if adding this file exceeds the total character budget
        if total_chars + block_len > max_total_diff_chars:
            remaining_budget = max_total_diff_chars - total_chars
            if remaining_budget > 200:
                truncated_block = (
                    f"\n==========================\nFILE: {filename} (TRUNCATED)\n"
                    f"STATUS: {status}\n==========================\n\n"
                    + patch[: remaining_budget - 150]
                    + "\n\n[DIFF TRUNCATED - OVERALL LIMIT REACHED]"
                )
                code_changes_blocks.append(truncated_block)
                included_count += 1
            break

        code_changes_blocks.append(file_block)
        total_chars += block_len
        included_count += 1

    return "".join(code_changes_blocks), included_count
