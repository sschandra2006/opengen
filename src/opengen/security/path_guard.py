"""
Path traversal and file safety guard.
"""
import os
from pathlib import Path
from opengen.config import settings
from opengen.domain.errors import SecurityViolationError

class PathGuard:
    """Enforces strict filesystem boundary containment."""

    @staticmethod
    def assert_safe_path(user_path: str, allow_absolute: bool = True) -> Path:
        """
        Resolves path and asserts it stays within the allowed workspace boundary.
        Prevents directory traversal attacks ('../') and symlink escapes.
        """
        p = Path(user_path).resolve()
        allowed_root = settings.BASE_DIR.resolve()

        if not p.is_relative_to(allowed_root):
            raise SecurityViolationError(
                f"Path traversal blocked: '{user_path}' resolves outside allowed workspace root."
            )

        # Check for malicious symlinks pointing outside
        if p.is_symlink():
            target = p.readlink().resolve()
            if not target.is_relative_to(allowed_root):
                raise SecurityViolationError("Symlink escape attempt blocked.")

        return p

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Removes dangerous characters and path traversal attempts from upload filenames."""
        basename = os.path.basename(filename)
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '_', basename)
        return sanitized or "unnamed_file"
