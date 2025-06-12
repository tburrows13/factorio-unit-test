#!/usr/bin/env python3
try:
    import _jsonnet
except ModuleNotFoundError as ex:
    print("Error: Importing jsonnet failed")
    print(
        "Please install the jsonnet package by running `pip install jsonnet` or `python3 -m pip install jsonnet`."
    )
    raise

import argparse
from pathlib import Path

from python.unit_test_controller import UnitTestController
from python.unit_test_configuration import UnitTestConfiguration


def main():
    parser = argparse.ArgumentParser(description="Factorio Unit Test CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run unit tests")
    run_parser.add_argument(
        "-f",
        "--factorio-path",
        type=str,
        help="Path to the Factorio executable. See https://wiki.factorio.com/Application_directory",
    )
    run_parser.add_argument(
        "-u",
        "--user-data-directory",
        type=str,
        help="Path to the user data directory. See https://wiki.factorio.com/Application_directory",
    )
    run_parser.add_argument(
        "-m",
        "--mod-directory",
        type=str,
        help="Path to the Factorio mods directory. Uses /mods in user data directory by default",
    )
    run_parser.add_argument(
        "-l",
        "--log",
        type=bool,
        nargs="?",
        const=True,
        default=False,
        help="Log output to file",
    )
    run_parser.add_argument("modname", type=str, help="The mod to test")

    args = parser.parse_args()

    if args.command == "run":
        factorioPath = (
            Path(args.factorio_path).expanduser().resolve()
            if args.factorio_path
            else None
        )
        userDataDirectory = (
            Path(args.user_data_directory).expanduser().resolve()
            if args.user_data_directory
            else None
        )
        modDirectory = (
            Path(args.mod_directory).expanduser().resolve()
            if args.mod_directory
            else None
        )
        logToFile = args.log
        modToTest = args.modname

        testController = UnitTestController(
            updateMods=False,
            factorioPath=factorioPath,
            userDataDirectory=userDataDirectory,
            modDirectory=modDirectory,
            logToFile=logToFile,
        )

        configFile = (
            testController.modDirectory / modToTest / "unit-test-config.jsonnet"
        )
        if not configFile.exists():
            raise FileNotFoundError(
                f"Configuration file {configFile} does not exist. Please ensure the mod has a valid unit test configuration."
            )
        testController.logger(f"Using configuration file: {configFile}")

        testConfigurations = UnitTestConfiguration(modToTest, configFile)
        testController.TestConfigurations(testConfigurations)


if __name__ == "__main__":
    main()
