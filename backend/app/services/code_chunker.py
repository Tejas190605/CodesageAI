import re
import hashlib
from typing import List, Dict, Any, Optional

# Standard Ignore Directories & Files
EXCLUDED_DIRECTORIES = {
    ".git", "node_modules", ".next", "dist", "build", "coverage",
    "venv", ".venv", "__pycache__", ".pytest_cache", ".idea", ".vscode"
}

EXCLUDED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf", ".zip",
    ".tar", ".gz", ".7z", ".exe", ".dll", ".so", ".dylib", ".db", ".sqlite",
    ".min.js", ".min.css", ".map", ".lock", "package-lock.json", "yarn.lock"
}

LANGUAGE_MAPPING = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "javascript",
    ".java": "java",
    ".go": "go",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
}


def is_file_excluded(file_path: str) -> bool:
    """Returns True if a file path matches binary, generated, or system ignore rules."""
    parts = file_path.replace("\\", "/").split("/")
    for part in parts:
        if part in EXCLUDED_DIRECTORIES:
            return True

    lower_path = file_path.lower()
    for ext in EXCLUDED_EXTENSIONS:
        if lower_path.endswith(ext):
            return True

    return False


def detect_language(file_path: str) -> str:
    """Detects programming language from file extension."""
    for ext, lang in LANGUAGE_MAPPING.items():
        if file_path.lower().endswith(ext):
            return lang
    return "text"


def calculate_chunk_hash(repository: str, file_path: str, symbol_name: Optional[str], content: str) -> str:
    """Generates deterministic SHA-256 hash for incremental chunk deduplication."""
    raw = f"{repository}:{file_path}:{symbol_name or 'block'}:{content.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ParsedChunk(BaseModel if False else object):
    def __init__(
        self,
        file_path: str,
        language: str,
        symbol_name: Optional[str],
        symbol_type: str,
        start_line: int,
        end_line: int,
        content: str
    ):
        self.file_path = file_path
        self.language = language
        self.symbol_name = symbol_name
        self.symbol_type = symbol_type
        self.start_line = start_line
        self.end_line = end_line
        self.content = content


def chunk_source_code(repository: str, file_path: str, content: str) -> List[Dict[str, Any]]:
    """
    Language-aware semantic code chunker extracting functions, classes, methods, structs,
    and interfaces with line-level accuracy and fallback line boundary splitting.
    """
    if is_file_excluded(file_path):
        return []

    language = detect_language(file_path)
    lines = content.splitlines()
    if not lines:
        return []

    chunks: List[Dict[str, Any]] = []

    # Semantic Chunking by Language Patterns
    if language == "python":
        pattern = re.compile(r"^(async\s+def|def|class)\s+([a-zA-Z0-9_]+)", re.MULTILINE)
        matches = list(pattern.finditer(content))
        if matches:
            for i, match in enumerate(matches):
                symbol_kind, symbol_name = match.group(1), match.group(2)
                symbol_type = "class" if symbol_kind == "class" else "function"
                start_offset = match.start()
                end_offset = matches[i + 1].start() if i + 1 < len(matches) else len(content)

                chunk_text = content[start_offset:end_offset].strip()
                start_line = content[:start_offset].count("\n") + 1
                end_line = start_line + chunk_text.count("\n")

                chunks.append({
                    "file_path": file_path,
                    "language": language,
                    "symbol_name": symbol_name,
                    "symbol_type": symbol_type,
                    "start_line": start_line,
                    "end_line": max(start_line, end_line),
                    "content": chunk_text,
                    "content_hash": calculate_chunk_hash(repository, file_path, symbol_name, chunk_text)
                })

    elif language in ("typescript", "javascript", "tsx"):
        pattern = re.compile(
            r"^(export\s+)?(async\s+)?(function|class|interface|type)\s+([a-zA-Z0-9_]+)",
            re.MULTILINE
        )
        matches = list(pattern.finditer(content))
        if matches:
            for i, match in enumerate(matches):
                symbol_type = match.group(3)
                symbol_name = match.group(4)
                start_offset = match.start()
                end_offset = matches[i + 1].start() if i + 1 < len(matches) else len(content)

                chunk_text = content[start_offset:end_offset].strip()
                start_line = content[:start_offset].count("\n") + 1
                end_line = start_line + chunk_text.count("\n")

                chunks.append({
                    "file_path": file_path,
                    "language": language,
                    "symbol_name": symbol_name,
                    "symbol_type": symbol_type,
                    "start_line": start_line,
                    "end_line": max(start_line, end_line),
                    "content": chunk_text,
                    "content_hash": calculate_chunk_hash(repository, file_path, symbol_name, chunk_text)
                })

    elif language in ("go", "java"):
        pattern = re.compile(
            r"^(func|type|struct|class|interface|public\s+class)\s+([a-zA-Z0-9_]+)",
            re.MULTILINE
        )
        matches = list(pattern.finditer(content))
        if matches:
            for i, match in enumerate(matches):
                symbol_type = match.group(1).replace("public ", "")
                symbol_name = match.group(2)
                start_offset = match.start()
                end_offset = matches[i + 1].start() if i + 1 < len(matches) else len(content)

                chunk_text = content[start_offset:end_offset].strip()
                start_line = content[:start_offset].count("\n") + 1
                end_line = start_line + chunk_text.count("\n")

                chunks.append({
                    "file_path": file_path,
                    "language": language,
                    "symbol_name": symbol_name,
                    "symbol_type": symbol_type,
                    "start_line": start_line,
                    "end_line": max(start_line, end_line),
                    "content": chunk_text,
                    "content_hash": calculate_chunk_hash(repository, file_path, symbol_name, chunk_text)
                })

    # Deterministic Line-Window Fallback Chunker if no top-level symbols extracted
    if not chunks:
        chunk_size = 50  # 50 lines per chunk
        for start_idx in range(0, len(lines), chunk_size):
            chunk_lines = lines[start_idx:start_idx + chunk_size]
            chunk_text = "\n".join(chunk_lines).strip()
            if not chunk_text:
                continue

            start_line = start_idx + 1
            end_line = start_idx + len(chunk_lines)
            symbol_name = f"{file_path}:L{start_line}-L{end_line}"

            chunks.append({
                "file_path": file_path,
                "language": language,
                "symbol_name": symbol_name,
                "symbol_type": "module_block",
                "start_line": start_line,
                "end_line": end_line,
                "content": chunk_text,
                "content_hash": calculate_chunk_hash(repository, file_path, symbol_name, chunk_text)
            })

    return chunks
