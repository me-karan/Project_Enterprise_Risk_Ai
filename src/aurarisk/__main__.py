"""
Command-line entry point for the AuraRisk package.

Run directly:

    uv run python -m aurarisk

Or through the project command:

    uv run aurarisk
"""

from aurarisk import __version__


def main() -> None:
    """
    Print basic application information.

    Later phases will replace this simple entry point with operational
    commands for running the API, generating data, training models, and
    evaluating investigations.
    """
    print("AuraRisk: AI Banking Risk and Fraud Investigation Platform")
    print(f"Version: {__version__}")
    print("Status: Engineering foundation initialized.")


if __name__ == "__main__":
    main()
