#!/usr/bin/python3
"""
This script builds the Redland package on specified remote hosts.

It fetches the package tarball and build script, executes the build
process remotely, and reports the build time.

Usage:
    python build_redland.py PROGRAM-TARBALL HOSTS...

Arguments:
    PROGRAM-TARBALL (str): The name of the Redland package tarball (e.g., redland-1.1.0.tar.gz).
    HOSTS (str)         : One or more comma-separated username@hostname pairs specifying the remote hosts.
"""

import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta

program_name = os.path.basename(__file__)  # Get program name from filename
logging.basicConfig(level=logging.INFO, format=f"{program_name}: %(message)s")


def run_command(cmd, userhost=None, timeout=None):
    """
    Executes a command locally or remotely via SSH.

    Args:
        cmd (str): The command to execute.
        userhost (str, optional): The hostname for remote execution. Defaults to None (local).
        timeout (int, optional): The timeout in seconds for the command execution. Defaults to None (no timeout).

    Returns:
        int: The exit code of the command.

    Raises:
        RuntimeError: If the command fails with a non-zero exit code.
    """

    cmd = cmd.split()
    if userhost:
        # Use -x for forwarding X11 if needed
        cmd = ['ssh', '-n', '-x', userhost] + cmd
        logging.info(f"Running '{cmd}' on {userhost}")
    else:
        logging.info(f"Running '{cmd}' locally")
    try:
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
            # Set timeout if provided
            if timeout:
                process.wait(timeout=timeout)
                if process.returncode is None:
                    raise TimeoutError(f"Command '{cmd}' timed out after {timeout} seconds")

            # Stream output with timestamps
            while True:
                out_line = process.stdout.readline()
                if out_line:
                    sys.stdout.write(out_line)
                err_line = process.stderr.readline()
                if err_line:
                    sys.stdout.write(err_line)
                if not out_line and not err_line:
                    break

            # Check return code after streaming
            returncode = process.wait()
            if returncode:
                raise subprocess.CalledProcessError(returncode, cmd)

    except (TimeoutError, subprocess.CalledProcessError) as e:
        logging.error(f"{datetime.now().isoformat()}: Error: {e}")
        raise RuntimeError("Command execution failed") from e

def transfer_file(local_path, remote_path, host):
    """
    Transfers a file from the local machine to a remote host via SCP.

    Args:
        local_path (str): The path to the local file.
        remote_path (str): The destination path on the remote host.
        host (str): The hostname or username@hostname of the remote host.

    Returns:
        int: The exit code of the SCP command.

    Raises:
        RuntimeError: If the SCP transfer fails.
    """

    cmd = ['scp', '-pq', local_path, f'{host}:{remote_path}']
    logging.info(f"Copying {local_path} to {remote_path} on {host} with '{cmd}'")

    try:
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return process.returncode
    except subprocess.CalledProcessError as e:
        logging.info(f"Error transferring {local_path} to {host}: {e.stdout}")
        raise RuntimeError("SCP transfer failed") from e

def build_on_host(tarball, userhost):
    """
    Builds the Redland package on a remote host.

    Args:
        tarball (str): path of tarball to build
        userhost (str): The username and hostname combination (e.g., "user@host").
    """

    host, username = userhost.split("@") if "@" in userhost else (userhost, None)

    # Validate package tarball format
    tarball_file = os.path.basename(tarball)
    tarball_pattern = r"^[-\w]+-\d\..*tar\.gz$"
    if not re.match(tarball_pattern, tarball_file):
        logging.info(f"Invalid package tarball format: {tarball_file}")
        return

    # Local paths (assuming the program and build-redland script are in the same directory)
    program_dir = os.path.dirname(os.path.realpath(__file__))
    bins_dir = os.path.join(os.environ["HOME"], "dev/redland/admin")

    # Check if tarball file exists
    if not os.path.exists(tarball):
        logging.info(f"Package tarball not found: {tarball}")
        return

    logging.info(f"Building on host {host} ({username})...")

    # Clear remote build directory
    run_command(f"rm -f ./build-redland {tarball}", userhost)

    # Transfer build-redland script and tarball
    transfer_file(f"{bins_dir}/build-redland", '.', userhost)
    transfer_file(f"{tarball}", '.', userhost)

    logging.info("Starting remote build...")
    start_time = datetime.now()

    # Execute build script remotely
    run_command(f"./build-redland {tarball_file}", userhost)

    end_time = datetime.now()
    build_time = end_time - start_time
    logging.info(f"Remote build ended after {build_time.total_seconds():.2f} seconds")

def main():
    """
    The main function parses arguments and starts building on specified hosts.
    """

    if len(sys.argv) < 3:
        logging.error(f"Usage: {sys.argv[0]} PROGRAM-TARBALL HOSTS...")
        sys.exit(1)

    tarball = sys.argv[1]
    userhosts = sys.argv[2:]

    for userhost in userhosts:
        build_on_host(tarball, userhost)

if __name__ == "__main__":
    main()
