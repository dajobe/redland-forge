"""
Version management module for Redland Forge.

This module provides the version information as a single source of truth.
For production, it uses importlib.metadata to read from installed package.
For development, it prioritizes reading pyproject.toml directly.
"""

import sys
from pathlib import Path


def _read_pyproject_version() -> str:
    """Read version directly from pyproject.toml."""
    try:
        # Try tomllib first (Python 3.11+)
        try:
            import tomllib
        except ImportError:
            # Fallback to tomli for Python 3.9-3.10
            import tomli as tomllib

        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return str(data["project"]["version"])
    except Exception:
        # Final fallback
        return "unknown"


def _is_development_mode() -> bool:
    """Check if we're running in development mode."""
    try:
        # Check if pyproject.toml exists (development indicator)
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            # Check if .git exists (another development indicator)
            git_path = pyproject_path.parent / ".git"
            if git_path.exists():
                return True
            # Check if we're running from source (not installed)
            # If the current file is within the project root, we're in dev mode
            project_root = pyproject_path.parent
            current_file = Path(__file__).resolve()
            return project_root in current_file.parents
        return False
    except Exception:
        return False


# Determine version based on environment
if _is_development_mode():
    # In development, always read from pyproject.toml
    __version__ = _read_pyproject_version()
else:
    # In production, try importlib.metadata first
    try:
        from importlib.metadata import version, PackageNotFoundError

        try:
            __version__ = version("redland-forge")
        except PackageNotFoundError:
            # Package not installed, fall back to pyproject.toml
            __version__ = _read_pyproject_version()

    except ImportError:
        # Python < 3.8, fall back to pyproject.toml parsing
        __version__ = _read_pyproject_version()


def get_version() -> str:
    """Get the current version string."""
    return __version__
