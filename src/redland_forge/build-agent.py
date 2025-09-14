#!/usr/bin/python3
"""
Build redland tarballs and check they work.

Intended to be called via build-redland-on.py
"""

import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


class Colors:
    """ANSI color codes for terminal output."""

    # Reset all formatting
    RESET = "\033[0m"

    # Text colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright text colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"

    # Text formatting
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"


# Global color setting
_color_forced = None  # None = auto, True = force, False = disable


def set_color_mode(mode: str) -> None:
    """Set color mode: 'auto', 'always', or 'never'."""
    global _color_forced
    if mode == "auto":
        _color_forced = None
    elif mode == "always":
        _color_forced = True
    elif mode == "never":
        _color_forced = False
    else:
        raise ValueError(
            f"Invalid color mode: {mode}. Use 'auto', 'always', or 'never'"
        )


def supports_color() -> bool:
    """Check if the terminal supports color output."""
    # Check if color is explicitly forced or disabled
    if _color_forced is not None:
        return _color_forced

    # Check if we're in a terminal
    if not sys.stdout.isatty():
        return False

    # Check for common color-supporting terminals
    term = os.environ.get("TERM", "")
    if term in ("xterm", "xterm-256color", "screen", "screen-256color", "linux"):
        return True

    # Check for common platforms
    platform = sys.platform
    if platform in ("linux", "darwin"):  # Linux and macOS
        return True

    return False


def colorize(text: str, color: str) -> str:
    """Add color to text if terminal supports it."""
    if supports_color():
        return f"{color}{text}{Colors.RESET}"
    return text


def setup_logging(no_print_hostname: bool = False) -> None:
    """Set up logging configuration with color support."""
    program_name = Path(__file__).name

    # Create a custom formatter that supports colors
    class ColoredFormatter(logging.Formatter):
        def format(self, record) -> str:
            # Add colors based on log level
            if record.levelno >= logging.ERROR:
                record.msg = colorize(f"{record.msg}", Colors.BRIGHT_RED)
            elif record.levelno >= logging.WARNING:
                record.msg = colorize(f"{record.msg}", Colors.BRIGHT_YELLOW)
            elif record.levelno >= logging.INFO:
                record.msg = colorize(f"{record.msg}", Colors.BRIGHT_GREEN)

            return super().format(record)

    # Set up handler with colored formatter
    handler = logging.StreamHandler()
    if no_print_hostname:
        handler.setFormatter(ColoredFormatter("%(message)s"))
    else:
        handler.setFormatter(
            ColoredFormatter(
                f"{colorize(program_name, Colors.BRIGHT_CYAN)}: %(message)s"
            )
        )

    # Configure logger
    logger = logging.getLogger()
    logger.handlers.clear()  # Remove any existing handlers
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def get_cpu_count() -> int:
    """Get the number of CPU cores available."""
    try:
        return os.cpu_count() or 1
    except AttributeError:
        # Fallback for older Python versions
        try:
            # Try nproc command
            result = subprocess.run(
                ["nproc"], capture_output=True, text=True, check=True
            )
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Try sysctl on macOS
                result = subprocess.run(
                    ["sysctl", "-n", "hw.ncpu"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return int(result.stdout.strip())
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to reading /proc/cpuinfo on Linux
                try:
                    with open("/proc/cpuinfo", "r") as f:
                        return len([line for line in f if line.startswith("processor")])
                except FileNotFoundError:
                    return 1


def find_gnu_make() -> str:
    """Find GNU make executable."""
    for make_cmd in ["gnumake", "gmake", "make"]:
        try:
            result = subprocess.run(
                [make_cmd, "--version"], capture_output=True, text=True, check=True
            )
            if "GNU Make" in result.stdout:
                return make_cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return "make"  # Fallback


def extract_package_info(tarball_path: str) -> Tuple[str, str, str]:
    """Extract package name, version, and directory name from tarball."""
    tarball_name = Path(tarball_path).name

    # Remove .tar.gz or .tar.bz2 extension
    dirname = re.sub(r"\.tar\.(gz|bz2|xz)$", "", tarball_name)

    # Extract package name (everything before the last dash-number)
    package_match = re.match(r"^(.+?)-[\d.]*$", dirname)
    package = package_match.group(1) if package_match else dirname

    # Extract version (everything after the last dash)
    version_match = re.search(r"-([\d.]*)$", dirname)
    version = version_match.group(1) if version_match else "unknown"

    return package, version, dirname


def run_command(
    cmd: List[str], cwd: Optional[str] = None, timeout: Optional[int] = None
) -> int:
    """Run a command and return exit code."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, timeout=timeout, capture_output=True, text=True, check=False
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        logging.error(f"Command timed out: {' '.join(cmd)}")
        return 1
    except Exception as e:
        logging.error(f"Command failed: {' '.join(cmd)} - {e}")
        return 1


def run_command_with_output(
    cmd: List[str], cwd: Optional[str] = None, timeout: Optional[int] = None
) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, timeout=timeout, capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logging.error(f"Command timed out: {' '.join(cmd)}")
        return 1, "", "Command timed out"
    except Exception as e:
        logging.error(f"Command failed: {' '.join(cmd)} - {e}")
        return 1, "", str(e)


def get_system_info() -> str:
    """Get system information."""
    try:
        result = subprocess.run(
            ["uname", "-srmn"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "Unknown system"


def get_gnu_arch(config_guess_path: str) -> str:
    """Get GNU architecture using config.guess."""
    try:
        result = subprocess.run(
            [config_guess_path], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown-unknown-unknown"


def get_cc_version() -> str:
    """Get C compiler version."""
    try:
        result = subprocess.run(
            ["cc", "--version"], capture_output=True, text=True, check=True
        )
        return result.stdout.split("\n")[0]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "Unknown compiler"


def extract_tarball(tarball_path: str, extract_dir: str) -> bool:
    """Extract tarball to directory."""
    try:
        with tarfile.open(tarball_path, "r:*") as tar:
            # Use filter argument for Python 3.12+, fallback for older versions
            try:
                tar.extractall(extract_dir, filter="data")
            except TypeError:
                # Fallback for older Python versions that don't support filter
                tar.extractall(extract_dir)
        return True
    except Exception as e:
        logging.error(f"Failed to extract tarball: {e}")
        return False


def find_config_guess(build_dir: str) -> Optional[str]:
    """Find config.guess file in build directory."""
    for subdir in ["", "build"]:
        config_guess = Path(build_dir) / subdir / "config.guess"
        if config_guess.exists():
            return str(config_guess)
    return None


def run_make_step(
    step_name: str,
    cmd: List[str],
    cwd: str,
    log_file: str,
    timeout: Optional[int] = None,
) -> bool:
    """Run a make step and log results."""
    start_time = datetime.now()

    logging.info(f"Running {step_name}...")

    # Create log directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Run command and capture output
    returncode, stdout, stderr = run_command_with_output(cmd, cwd=cwd, timeout=timeout)

    # Write output to log file
    with open(log_file, "w") as f:
        f.write(f"Command: {' '.join(cmd)}\n")
        f.write(f"Working directory: {cwd}\n")
        f.write(f"Return code: {returncode}\n")
        f.write(f"Start time: {start_time}\n")
        f.write(f"End time: {datetime.now()}\n")
        f.write("\n" + "=" * 80 + "\nSTDOUT\n" + "=" * 80 + "\n")
        f.write(stdout)
        f.write("\n" + "=" * 80 + "\nSTDERR\n" + "=" * 80 + "\n")
        f.write(stderr)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    if returncode == 0:
        logging.info(
            colorize(
                f"{step_name} succeeded ({duration:.1f} secs)", Colors.BRIGHT_GREEN
            )
        )

        # Show compiler warnings if any
        warnings = re.findall(r"^[A-Za-z0-9_]+\.c.*warning", stdout, re.MULTILINE)
        if warnings:
            logging.warning(f"Compiler warnings found in {step_name}:")
            for warning in warnings[:10]:  # Show first 10 warnings
                logging.warning(f"  {warning}")
            if len(warnings) > 10:
                logging.warning(f"  ... and {len(warnings) - 10} more warnings")

        return True
    else:
        logging.error(
            colorize(f"{step_name} failed ({duration:.1f} secs)", Colors.BRIGHT_RED)
        )

        # Show relevant error messages
        if "configure" in step_name.lower():
            errors = re.findall(r"^configure: error.*", stdout, re.MULTILINE)
        elif "check" in step_name.lower():
            errors = re.findall(r"^FAIL:.*", stdout, re.MULTILINE)
        else:
            errors = re.findall(r"^make.*error.*", stdout, re.MULTILINE)

        if errors:
            for error in errors[:5]:  # Show first 5 errors
                logging.error(f"  {error}")
            if len(errors) > 5:
                logging.error(f"  ... and {len(errors) - 5} more errors")

        return False


def build_language_bindings(
    build_dir: str,
    logs_dir: str,
    make_cmd: str,
    languages: List[str],
) -> Tuple[List[str], List[str]]:
    """Build language bindings and return lists of successful and failed languages."""
    successful = []
    failed = []

    for lang in languages:
        lang_dir = Path(build_dir) / lang
        if not lang_dir.exists():
            continue

        logging.info(f"Building {lang} bindings...")
        start_time = datetime.now()

        # Run make check for language binding
        cmd = [make_cmd, "-j1", "check"]
        returncode, stdout, stderr = run_command_with_output(cmd, cwd=str(lang_dir))

        # Write log
        log_file = Path(logs_dir) / f"{lang}.log"
        with open(log_file, "w") as f:
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write(f"Working directory: {lang_dir}\n")
            f.write(f"Return code: {returncode}\n")
            f.write(f"Start time: {start_time}\n")
            f.write(f"End time: {datetime.now()}\n")
            f.write("\n" + "=" * 80 + "\nSTDOUT\n" + "=" * 80 + "\n")
            f.write(stdout)
            f.write("\n" + "=" * 80 + "\nSTDERR\n" + "=" * 80 + "\n")
            f.write(stderr)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if returncode == 0:
            logging.info(
                colorize(
                    f"{lang} bindings built successfully ({duration:.1f} secs)",
                    Colors.BRIGHT_GREEN,
                )
            )
            successful.append(lang)
        else:
            logging.warning(
                colorize(
                    f"{lang} bindings failed ({duration:.1f} secs)",
                    Colors.BRIGHT_YELLOW,
                )
            )
            failed.append(lang)

    return successful, failed


def main() -> int:
    """Main build function."""
    # Parse arguments
    args = sys.argv[1:]
    tarball_path = None
    no_print_hostname = False
    bindings_languages = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--no-print-hostname":
            no_print_hostname = True
            i += 1
        elif arg == "--bindings-languages":
            if i + 1 < len(args):
                bindings_languages = args[i + 1].split(",")
                i += 2
            else:
                logging.error("--bindings-languages requires an argument")
                return 1
        elif tarball_path is None:
            tarball_path = arg
            i += 1
        else:
            logging.error(f"Unknown argument: {arg}")
            return 1

    if tarball_path is None:
        logging.error(
            "USAGE: build-agent.py PACKAGE-TARBALL [--no-print-hostname] [--bindings-languages LUA,PERL,...]"
        )
        return 1

    # Set up logging based on hostname preference
    setup_logging(no_print_hostname)

    # Check if tarball exists
    if not Path(tarball_path).exists():
        logging.error(f"Tarball {tarball_path} not found")
        return 1

    # Extract package information
    package, version, dirname = extract_package_info(tarball_path)

    # Get system information
    ncpus = get_cpu_count()
    system_info = get_system_info()
    make_cmd = find_gnu_make()

    # Setup working directories
    here = Path.cwd()
    working = here / "build"
    logs = working / "logs"
    build = working / dirname
    install = working / "install"

    # Ensure tarball path is absolute
    if not Path(tarball_path).is_absolute():
        tarball_path = str(here / tarball_path)

    # Clean and create working directories
    if working.exists():
        shutil.rmtree(working)
    working.mkdir(parents=True)
    logs.mkdir()
    install.mkdir()

    # Print build information
    logging.info(f"Building {package} {version}")
    logging.info(f"System       {system_info}")
    logging.info(f"CPUs         {ncpus}")
    logging.info(f"Working area {working}")
    logging.info(f"Logs         {logs}")

    start_time = datetime.now()

    # Extract tarball
    logging.info("Extracting tarball...")
    if not extract_tarball(tarball_path, str(working)):
        return 1

    # Change to build directory
    if not build.exists():
        logging.error(f"Build directory {build} not found after extraction")
        return 1

    # Find config.guess
    config_guess = find_config_guess(str(build))
    if config_guess:
        gnu_arch = get_gnu_arch(config_guess)
        logging.info(f"GNU System   {gnu_arch}")
    else:
        logging.warning("config.guess not found")
        gnu_arch = "unknown-unknown-unknown"

    # Get compiler version
    cc_version = get_cc_version()
    logging.info(f"CC Version   {cc_version}")

    # Configure
    configure_cmd = ["./configure", f"--prefix={install}"]
    if not run_make_step(
        "configure", configure_cmd, str(build), str(logs / "configure.log")
    ):
        return 1

    # Show configure build summary if available
    configure_log = logs / "configure.log"
    if configure_log.exists():
        with open(configure_log, "r") as f:
            content = f.read()
            # Extract build summary section
            import re

            summary_match = re.search(
                r"build summary:.*?(?=\n\n|\Z)", content, re.DOTALL
            )
            if summary_match:
                logging.info("Configure build summary:")
                for line in summary_match.group(0).split("\n"):
                    if line.strip():
                        logging.info(f"  {line.strip()}")

    # Make
    make_cmd_list = [make_cmd, f"-j{ncpus}"]
    if not run_make_step("make", make_cmd_list, str(build), str(logs / "make.log")):
        return 1

    # Make check
    make_check_cmd = [make_cmd, f"-j{ncpus}", "check"]
    if not run_make_step(
        "make check", make_check_cmd, str(build), str(logs / "make-check.log")
    ):
        return 1

    # Make install
    make_install_cmd = [make_cmd, "install"]
    if not run_make_step(
        "make install", make_install_cmd, str(build), str(logs / "make-install.log")
    ):
        return 1

    # To prevent parallel 'make check' errors, until all tests are
    # converted to automake parallel test friendly form.
    if "MAKEFLAGS" in os.environ:
        del os.environ["MAKEFLAGS"]

    successful_langs: List[str] = []
    failed_langs: List[str] = []
    if bindings_languages:
        # Build language bindings
        successful_langs, failed_langs = build_language_bindings(
            str(build), str(logs), make_cmd, bindings_languages
        )

    # Print summary
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    if not successful_langs and not failed_langs:
        logging.info("No language interfaces to build")
    else:
        logging.info("Summary of language interface builds:")
        if successful_langs:
            logging.info(
                colorize(f"  OK      {' '.join(successful_langs)}", Colors.BRIGHT_GREEN)
            )
        if failed_langs:
            logging.warning(
                colorize(f"  FAILED  {' '.join(failed_langs)}", Colors.BRIGHT_YELLOW)
            )

    logging.info(
        colorize(f"Total time taken: {total_duration:.1f} secs", Colors.BRIGHT_CYAN)
    )

    # Return success if no language bindings failed
    return 0 if not failed_langs else 1


if __name__ == "__main__":
    # Exit with appropriate code
    sys.exit(main())
