#!/usr/bin/python3
"""
Build Redland Text UI - Entry Point

Thin wrapper script for the parallel build monitoring TUI.
"""

import argparse
import logging
import sys
from typing import List

from app import BuildTUI, set_color_mode, read_hosts_from_file
from config import Config
from exception_handler import ExceptionHandler


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Build Redland package on remote hosts with TUI monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s redland-1.1.0.tar.gz user1@host1 user2@host2
  %(prog)s redland-1.1.0.tar.gz -f hosts.txt
  %(prog)s redland-1.1.0.tar.gz --max-concurrent 6 user1@host1,user2@host2

Hosts file format:
  # Comments start with #
  user1@host1
  user2@host2
  # Blank lines are ignored
  user3@host3
""",
    )
    parser.add_argument(
        "tarball",
        nargs="?",
        help="The Redland package tarball (e.g., redland-1.1.0.tar.gz)",
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
        "--max-concurrent",
        type=int,
        help="Maximum concurrent builds (default: auto-detect based on screen size)",
    )
    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Control color output: auto (default), always, or never",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to debug.log file",
    )
    parser.add_argument(
        "--auto-exit-delay",
        type=int,
        default=300,
        help="Auto-exit delay in seconds after last build completes (default: 300 = 5 minutes)",
    )
    parser.add_argument(
        "--no-auto-exit",
        action="store_true",
        help="Disable auto-exit functionality",
    )

    # Timing cache options
    parser.add_argument(
        "--cache-file",
        type=str,
        help="Custom cache file location (default: .config/build-tui/timing-cache.json)",
    )
    parser.add_argument(
        "--cache-retention",
        type=int,
        default=30,
        help="Cache retention period in days (default: 30)",
    )
    parser.add_argument(
        "--cache-keep-builds",
        type=int,
        default=5,
        help="Number of recent builds to keep in cache (default: 5)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable timing cache functionality",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress display",
    )

    parser.add_argument(
        "--cleanup-demo-hosts",
        action="store_true",
        help="Clean up demo/test host data from timing cache and exit",
    )
    parser.add_argument(
        "--remove-testing-hosts",
        action="store_true",
        help="Remove specific testing hosts from timing cache and exit",
    )
    parser.add_argument(
        "--bindings-languages",
        type=str,
        help="Comma-separated list of language bindings to build.",
    )

    args = parser.parse_args()

    # Validate that we have either hosts or hosts-file (unless cleaning up demo hosts)
    if (
        not args.cleanup_demo_hosts
        and not args.remove_testing_hosts
        and not args.hosts
        and not args.hosts_file
    ):
        parser.error("Either hosts or --hosts-file must be specified")

    return args


def format_host_table(hosts: List[str]) -> str:
    """Formats the host list into a text table with a border."""
    if not hosts:
        return "No hosts."

    max_to_show = 5
    num_hosts = len(hosts)

    hosts_to_show = hosts[:max_to_show]

    title = f" Starting TUI with {num_hosts} hosts "

    # Determine the width of the table
    max_len = max(len(h) for h in hosts_to_show) if hosts_to_show else 0
    width = max(max_len, len(title)) + 4

    # Top border
    table = ["┌" + "─" * (width - 2) + "┐"]

    # Title
    title_padding = (width - 2 - len(title)) // 2
    table.append(
        "│"
        + " " * title_padding
        + title
        + " " * (width - 2 - len(title) - title_padding)
        + "│"
    )

    # Separator
    table.append("├" + "─" * (width - 2) + "┤")

    # Host list
    for host in hosts_to_show:
        padded_host = f"  {host}".ljust(width - 2)
        table.append("│" + padded_host + "│")

    if num_hosts > max_to_show:
        more_text = f"  ... and {num_hosts - max_to_show} more."
        padded_more = more_text.ljust(width - 2)
        table.append("│" + padded_more + "│")

    # Bottom border
    table.append("└" + "─" * (width - 2) + "┘")

    return "\n".join(table)


def main() -> int:
    """Main function."""
    try:
        args = parse_arguments()
    except SystemExit:
        return 1

    # Handle demo host cleanup if requested (before logging setup)
    if args.cleanup_demo_hosts:
        try:
            from build_timing_cache import BuildTimingCache

            cache = BuildTimingCache()
            cache.clear_demo_hosts()
            print("Demo host data cleaned up successfully")
            return 0
        except Exception as e:
            print(f"Error cleaning up demo hosts: {e}")
            return 1

    # Handle testing host removal if requested (before logging setup)
    if args.remove_testing_hosts:
        try:
            from build_timing_cache import BuildTimingCache

            cache = BuildTimingCache()
            cache.remove_testing_hosts()
            print("Testing host data removed successfully")
            return 0
        except Exception as e:
            print(f"Error removing testing hosts: {e}")
            return 1

    # Set up logging to debug.log by default
    logging.basicConfig(
        level=Config.DEBUG_LOG_LEVEL if args.debug else Config.DEFAULT_LOG_LEVEL,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(Config.LOG_FILE),
            # Never add console handler - debug logs only go to file
            logging.NullHandler(),
        ],
    )

    if args.debug:
        logging.debug("Debug logging enabled")
    else:
        logging.info("Logging to debug.log (use --debug for console output)")

    # Set color mode
    set_color_mode(args.color)

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

    # Clean up hosts list
    userhosts = [host.strip() for host in userhosts if host.strip()]

    if not userhosts:
        logging.error("No valid hosts specified")
        return 1

    # Create and run TUI
    try:
        print(format_host_table(userhosts))
        logging.debug("About to create BuildTUI instance")

        # Prepare auto-exit options
        auto_exit_delay = None if args.no_auto_exit else args.auto_exit_delay
        auto_exit_enabled = not args.no_auto_exit

        # Prepare timing cache options
        cache_file = args.cache_file
        cache_retention = args.cache_retention
        cache_keep_builds = args.cache_keep_builds
        cache_enabled = not args.no_cache
        progress_enabled = not args.no_progress

        bindings_languages = (
            args.bindings_languages.split(",") if args.bindings_languages else None
        )

        tui = BuildTUI(
            userhosts,
            args.tarball,
            args.max_concurrent,
            auto_exit_delay=auto_exit_delay,
            auto_exit_enabled=auto_exit_enabled,
            cache_file=cache_file,
            cache_retention=cache_retention,
            cache_keep_builds=cache_keep_builds,
            cache_enabled=cache_enabled,
            progress_enabled=progress_enabled,
            bindings_languages=bindings_languages,
        )
        logging.debug("BuildTUI instance created successfully, about to call run()")
        tui.run()
        logging.debug("BuildTUI.run() completed successfully")
    except FileNotFoundError as e:
        # Handle file not found errors with a clean message
        logging.error(f"File not found: {e}")
        print(f"Error: {e}")
        return 1
    except Exception as e:
        import traceback

        exception_results = ExceptionHandler.handle_exception(
            e, "Main application error", show_user=True
        )
        print(f"\n{ExceptionHandler.format_exception_summary(exception_results)}")
        print("Full traceback:")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
