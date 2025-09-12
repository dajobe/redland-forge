#!/usr/bin/python3
"""
This script builds the Redland package on specified remote hosts.

It fetches the package tarball and build script, executes the build
process remotely, and reports the build time.

Usage:
    python build_redland.py PROGRAM-TARBALL HOSTS...
    python build_redland.py PROGRAM-TARBALL -f HOSTS_FILE

Arguments:
    PROGRAM-TARBALL (str): The name of the Redland package tarball
                           (e.g., redland-1.1.0.tar.gz).
    HOSTS (str)         : One or more comma-separated username@hostname
                          pairs specifying the remote hosts.
    -f HOSTS_FILE       : Read hosts from file, one per line.
                          Lines starting with # or blank lines are ignored.
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List


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


def setup_logging() -> None:
    """Set up logging configuration with color support."""
    program_name = Path(__file__).name

    # Create a custom formatter that supports colors
    class ColoredFormatter(logging.Formatter):
        def format(self, record):
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
    handler.setFormatter(
        ColoredFormatter(f"{colorize(program_name, Colors.BRIGHT_CYAN)}: %(message)s")
    )

    # Configure logger
    logger = logging.getLogger()
    logger.handlers.clear()  # Remove any existing handlers
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def run_command(cmd: str, userhost: str = None, timeout: int = None) -> int:
    """
    Execute a command locally or remotely via SSH.

    Args:
        cmd: The command to execute.
        userhost: The hostname for remote execution. Defaults to None (local).
        timeout: The timeout in seconds for the command execution.
                 Defaults to None (no timeout).

    Returns:
        The exit code of the command.

    Raises:
        RuntimeError: If the command fails with a non-zero exit code.
    """
    cmd_parts = cmd.split()
    if userhost:
        # Use -x for forwarding X11 if needed
        cmd_parts = ["ssh", "-n", "-x", userhost] + cmd_parts
        logging.debug(f"Running '{cmd}' on {userhost}")
    else:
        logging.debug(f"Running '{cmd}' locally")

    try:
        # Use subprocess.Popen with unbuffered output for real-time streaming
        with subprocess.Popen(
            cmd_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,  # Unbuffered
            universal_newlines=True,
        ) as process:
            # Set timeout if provided
            if timeout:
                process.wait(timeout=timeout)
                if process.returncode is None:
                    raise TimeoutError(
                        f"Command '{cmd}' timed out after {timeout} seconds"
                    )

            # Stream output in real-time
            import select
            import sys

            # Get file descriptors for non-blocking reads
            stdout_fd = process.stdout.fileno()
            stderr_fd = process.stderr.fileno()

            # Set non-blocking mode
            import os
            import fcntl

            for fd in [stdout_fd, stderr_fd]:
                flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            # Color the hostname for output - use a light pastel color
            host_color = Colors.BRIGHT_CYAN
            host_prefix = colorize(f"{userhost}>", host_color)
            stderr_prefix = colorize(f"{userhost}>[STDERR]", Colors.BRIGHT_YELLOW)

            # Read output until process completes
            while process.poll() is None:
                # Check for available output
                ready, _, _ = select.select(
                    [process.stdout, process.stderr], [], [], 0.1
                )

                for stream in ready:
                    try:
                        line = stream.readline()
                        if line:
                            if stream == process.stdout:
                                sys.stdout.write(f"{host_prefix} {line}")
                            else:
                                sys.stdout.write(f"{stderr_prefix} {line}")
                            sys.stdout.flush()  # Force immediate output
                    except (IOError, OSError):
                        # No more data available
                        pass

            # Read any remaining output
            for stream, prefix in [
                (process.stdout, f"{host_prefix} "),
                (process.stderr, f"{stderr_prefix} "),
            ]:
                try:
                    while True:
                        line = stream.readline()
                        if not line:
                            break
                        sys.stdout.write(f"{prefix}{line}")
                        sys.stdout.flush()
                except (IOError, OSError):
                    pass

            return process.wait()

    except (TimeoutError, subprocess.CalledProcessError) as e:
        logging.error(f"{datetime.now().isoformat()}: Error: {e}")
        raise RuntimeError("Command execution failed") from e


def transfer_file(local_path: str, remote_path: str, host: str) -> int:
    """
    Transfer a file from the local machine to a remote host via SCP.

    Args:
        local_path: The path to the local file.
        remote_path: The destination path on the remote host.
        host: The hostname or username@hostname of the remote host.

    Returns:
        The exit code of the SCP command.

    Raises:
        RuntimeError: If the SCP transfer fails.
    """
    cmd = ["scp", "-pq", local_path, f"{host}:{remote_path}"]
    logging.debug(f"Copying {local_path} to {remote_path} on {host} with '{cmd}'")

    try:
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return process.returncode
    except subprocess.CalledProcessError as e:
        logging.info(f"Error transferring {local_path} to {host}: {e.stdout}")
        raise RuntimeError("SCP transfer failed") from e


def read_hosts_from_file(filename: str) -> List[str]:
    """
    Read hosts from a file, one per line.

    Args:
        filename: Path to the file containing hosts.

    Returns:
        List of host strings, with comments and blank lines removed.

    Raises:
        FileNotFoundError: If the hosts file doesn't exist.
    """
    hosts = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip blank lines and comments
                if not line or line.startswith("#"):
                    continue
                hosts.append(line)
    except FileNotFoundError:
        logging.error(f"Hosts file not found: {filename}")
        raise

    if not hosts:
        logging.warning(f"No valid hosts found in {filename}")

    return hosts


def detect_bindings_languages(tarball: str) -> str:
    """
    Detect which language binding directories exist in the tarball.

    Args:
        tarball: Path to the tarball file.

    Returns:
        Comma-separated string of detected language bindings.
    """
    import tempfile
    import tarfile

    detected_languages = []

    try:
        # Create a temporary directory to extract just the directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            with tarfile.open(tarball, "r:*") as tar:
                # Extract only the top-level directories to check for language bindings
                for member in tar.getmembers():
                    if member.isdir() and "/" not in member.name.rstrip("/"):
                        # Top-level directory, check if it's a language binding
                        lang = member.name.rstrip("/")
                        if lang in ["perl", "python", "ruby", "php", "lua"]:
                            detected_languages.append(lang)

    except Exception as e:
        logging.warning(f"Failed to detect language bindings from tarball: {e}")
        # Fall back to all languages if detection fails
        return "perl,python,ruby,php,lua"

    if not detected_languages:
        logging.debug("No language bindings detected in tarball")
        return ""

    languages_str = ",".join(detected_languages)
    logging.debug(f"Detected language bindings: {languages_str}")
    return languages_str


def build_on_host(tarball: str, userhost: str) -> int:
    """
    Build the Redland package on a remote host.

    Args:
        tarball: Path of tarball to build.
        userhost: The username and hostname combination (e.g., "user@host").

    Returns:
        Exit code from the build process.
    """
    host, username = userhost.split("@") if "@" in userhost else (userhost, None)
    host_label = f"{host} " + (f"({username})" if username else "")

    # Validate package tarball format
    tarball_file = Path(tarball).name
    tarball_pattern = r"^[-\w]+-\d\..*tar\.gz$"
    if not re.match(tarball_pattern, tarball_file):
        logging.info(f"Invalid package tarball format: {tarball_file}")
        return 1

    # Local paths (assuming the program and build-agent script are in the
    # same directory)
    program_dir = Path(__file__).parent
    bins_dir = program_dir

    # Check if tarball file exists
    if not Path(tarball).exists():
        logging.info(f"Package tarball not found: {tarball}")
        return 1

    # Detect which language bindings are available in the tarball
    bindings_languages = detect_bindings_languages(tarball)
    bindings_arg = f" --bindings-languages {bindings_languages}" if bindings_languages else ""

    logging.info(f"Building on {colorize(host_label, Colors.BRIGHT_CYAN)}...")
    if bindings_languages:
        logging.debug(f"Language bindings to build: {bindings_languages}")

    # Clear remote build directory
    run_command(f"rm -f ./build-agent.py {tarball}", userhost)

    # Transfer build-agent.py script and tarball
    transfer_file(str(bins_dir / "build-agent.py"), ".", userhost)
    transfer_file(tarball, ".", userhost)

    logging.info(colorize("Starting remote build...", Colors.BRIGHT_BLUE))
    start_time = datetime.now()

    # Execute build script remotely with detected language bindings
    rc = run_command(
        f"python3 ./build-agent.py {tarball_file} --no-print-hostname{bindings_arg}", userhost
    )

    end_time = datetime.now()
    build_time = end_time - start_time

    if rc == 0:
        logging.info(
            colorize(
                f"Remote build completed successfully after {build_time.total_seconds():.2f} seconds",
                Colors.BRIGHT_GREEN,
            )
        )
    else:
        logging.warning(
            f"Remote build failed after {build_time.total_seconds():.2f} seconds with code {rc}"
        )
    return rc


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Build the Redland package on specified remote hosts. "
        "It fetches the package tarball and build script, executes the build "
        "process remotely, and reports the build time.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s redland-1.1.0.tar.gz user1@host1 user2@host2
  %(prog)s redland-1.1.0.tar.gz -f hosts.txt
  %(prog)s redland-1.1.0.tar.gz user1@host1,user2@host2
  %(prog)s redland-1.1.0.tar.gz --color always user1@host1
  %(prog)s redland-1.1.0.tar.gz --color never -f hosts.txt

Hosts file format:
  # Comments start with #
  user1@host1
  user2@host2
  # Blank lines are ignored
  user3@host3
""",
    )
    parser.add_argument(
        "tarball", help="The Redland package tarball (e.g., redland-1.1.0.tar.gz)"
    )
    parser.add_argument(
        "hosts",
        nargs="*",
        help="One or more username@hostname pairs. Can be comma-separated.",
    )
    parser.add_argument(
        "-f",
        "--hosts-file",
        help="Read hosts from file, one per line. Lines starting with # or blank lines are ignored.",
    )
    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Control color output: auto (default), always, or never",
    )

    args = parser.parse_args()

    # Validate that we have either hosts or hosts-file
    if not args.hosts and not args.hosts_file:
        parser.error("Either hosts or --hosts-file must be specified")

    return args


def main() -> int:
    """Main function to parse arguments and start building on specified hosts."""
    try:
        args = parse_arguments()
    except SystemExit:
        return 1

    # Set color mode before setting up logging
    set_color_mode(args.color)
    setup_logging()

    tarball = args.tarball

    # Get hosts list
    if args.hosts_file:
        try:
            userhosts = read_hosts_from_file(args.hosts_file)
        except FileNotFoundError:
            return 1
    else:
        # Split comma-separated hosts if provided as single string
        userhosts = []
        for host_arg in args.hosts:
            userhosts.extend(host_arg.split(","))

    results = {}
    for userhost in userhosts:
        userhost = userhost.strip()
        if userhost:  # Skip empty strings
            results[userhost] = build_on_host(tarball, userhost)

    logging.info(f"Summary of build of {colorize(tarball, Colors.BRIGHT_CYAN)}")

    # Count results for summary
    success_count = sum(1 for rc in results.values() if rc == 0)
    fail_count = len(results) - success_count

    for host in sorted(results.keys()):
        rc = results[host]
        host_colored = colorize(host, Colors.BRIGHT_CYAN)

        if not rc:
            status = colorize("✓ Success", Colors.BRIGHT_GREEN)
        else:
            status = colorize(f"✗ FAIL (code {rc})", Colors.BRIGHT_RED)
        print(f"  {host_colored:20s}: {status}")

    # Print summary statistics
    if success_count > 0:
        success_msg = colorize(f"{success_count} successful", Colors.BRIGHT_GREEN)
        print(f"\n{success_msg}")

    if fail_count > 0:
        fail_msg = colorize(f"{fail_count} failed", Colors.BRIGHT_RED)
        print(f"{fail_msg}")

    if success_count == len(results):
        print(colorize("\n🎉 All builds completed successfully!", Colors.BRIGHT_GREEN))
    elif fail_count == len(results):
        print(colorize("\n💥 All builds failed!", Colors.BRIGHT_RED))
    else:
        print(
            colorize(
                f"\n⚠️  {fail_count}/{len(results)} builds failed", Colors.BRIGHT_YELLOW
            )
        )

    return 1 if any(rc != 0 for rc in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
