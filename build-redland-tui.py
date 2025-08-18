#!/usr/bin/python3
"""
Build Redland Text UI - Entry Point

Thin wrapper script for the parallel build monitoring TUI.
"""

import argparse
import logging
import sys

from app import BuildTUI, set_color_mode, read_hosts_from_file
from config import Config


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
        default=1,
        help="Cache retention period in days (default: 1)",
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

    args = parser.parse_args()

    # Validate that we have either hosts or hosts-file (unless cleaning up demo hosts)
    if not args.cleanup_demo_hosts and not args.hosts and not args.hosts_file:
        parser.error("Either hosts or --hosts-file must be specified")

    return args


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
        print(
            f"Starting TUI with {len(userhosts)} hosts: {userhosts[:3]}{'...' if len(userhosts) > 3 else ''}"
        )
        logging.debug("About to create BuildTUI instance")

        # Prepare auto-exit options
        auto_exit_delay = None if args.no_auto_exit else args.auto_exit_delay
        auto_exit_enabled = not args.no_auto_exit

        # Prepare timing cache options
        cache_file = args.cache_file
        cache_retention = args.cache_retention
        cache_enabled = not args.no_cache
        progress_enabled = not args.no_progress

        tui = BuildTUI(
            userhosts,
            args.tarball,
            args.max_concurrent,
            auto_exit_delay=auto_exit_delay,
            auto_exit_enabled=auto_exit_enabled,
            cache_file=cache_file,
            cache_retention=cache_retention,
            cache_enabled=cache_enabled,
            progress_enabled=progress_enabled,
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

        logging.error(f"Error in main function: {e}")
        logging.error("Full traceback:")
        logging.error(traceback.format_exc())
        print(f"Error in main function: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
