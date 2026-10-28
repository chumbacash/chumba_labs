from dotenv import load_dotenv

load_dotenv()

import argparse
import json

from api.routes import hplc_demo_run, health


def main() -> None:
    parser = argparse.ArgumentParser(prog="chumba-labs")
    parser.add_argument(
        "command",
        choices=("health", "hplc-demo"),
        default="hplc-demo",
        nargs="?",
        help="health | hplc-demo",
    )
    args = parser.parse_args()

    if args.command == "health":
        print(json.dumps(health(), indent=2))
        return

    print(json.dumps(hplc_demo_run(), indent=2))


if __name__ == "__main__":
    main()
