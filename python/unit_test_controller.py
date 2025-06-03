from __future__ import annotations
from typing import Optional
import os, sys, shutil, argparse

from mod_builder import ModBuilder
from mod_downloader import ModDownloader
from modlist_controller import ModlistController
from settings_controller import SettingsController
from factorio_controller import FactorioController
from unit_test_configuration import UnitTestConfiguration
from unit_test_logger import UnitTestLogger


class UnitTestController:
    def __init__(
        self,
        updateMods: bool = True,
        factorioInstallDir: Optional[str] = None,
        factorioFolderDir: Optional[str] = None,
        logToFile: bool = False,
        factorioModDir: Optional[str] = None,
    ):
        if factorioFolderDir is None:
            self.factorioFolderDir: str = os.path.abspath(
                f"{os.getenv('APPDATA')}/Factorio/"
            )
        else:
            self.factorioFolderDir: str = os.path.abspath(factorioFolderDir)

        #if updateMods:  # TODO
        #    self.__buildAngelsMods()
        #    self.__buildBobsMods()

        # Backup the current mod config and mod settings
        self.currentModlistController = ModlistController(
            self.factorioFolderDir, factorioModDir
        )
        self.currentModlistController.readConfigurationFile()
        self.currentSettingsController = SettingsController(
            self.factorioFolderDir, factorioModDir
        )
        self.currentSettingsController.readSettingsFile()

        # Logger for unit test output
        self.logger = UnitTestLogger(logToFile)

        # New controllers for the unit tests
        self.modlistController = ModlistController(
            self.factorioFolderDir, factorioModDir
        )
        self.settingsController = SettingsController(
            self.factorioFolderDir, factorioModDir
        )
        self.factorioController = FactorioController(
            factorioInstallDir, self.logger, factorioModDir
        )

    def close(self):
        # Reset mod config and mod settings to the backed up values
        self.currentModlistController.disableMod("factorio-unit-test")
        self.currentModlistController.writeConfigurationFile()
        self.currentSettingsController.writeSettingsFile()

    def TestConfigurations(
        self,
        testConfigurations: UnitTestConfiguration,
        logSummary: bool = True,
    ) -> None:
        testResults: dict[str, bool] = dict()
        for configName, config in testConfigurations:
            self.__logTestConfiguration(configName)
            self.__setupTestConfiguration(config["mods"], config["settings"])
            self.__setupTestFiles(testConfigurations.modName, testConfigurations.tests)
            testResults[configName] = self.__executeUnitTests()
        if logSummary:
            self.logger("Summary:", leading_newline=True)
            for testName, testResult in testResults.items():
                self.logger(f"[{'PASSED' if testResult else 'FAILED'}] {testName}")

    def __buildAngelsMods(self) -> None:
        ModBuilder(self.factorioFolderDir).createAllMods()

    def __buildBobsMods(self) -> None:
        bobmods = {
            "bobassembly": True,
            "bobclasses": True,
            "bobelectronics": True,
            "bobenemies": True,
            "bobequipment": True,
            "bobgreenhouse": True,
            "bobinserters": True,
            "boblibrary": True,
            "boblogistics": True,
            "bobmining": True,
            "bobmodules": True,
            "bobores": True,
            "bobplates": True,
            "bobpower": True,
            "bobrevamp": True,
            "bobtech": True,
            "bobvehicleequipment": True,
            "bobwarfare": True,
        }
        for name, download in bobmods.items():
            if download:
                ModDownloader(name, self.factorioFolderDir).download()

    def __logTestConfiguration(self, configName: str) -> None:
        self.logger(f"Testing {configName}", True)

    def __setupTestConfiguration(
        self, modList: list[str], settingCustomisation: dict[str, dict[str, bool]]
    ) -> None:
        # Configure Mods
        self.modlistController.readConfigurationFile()
        self.modlistController.disableAllMods()
        for modName in modList:
            self.modlistController.enableMod(modName)
        if "factorio-unit-test" not in modList:
            self.modlistController.enableMod("factorio-unit-test")
        self.modlistController.writeConfigurationFile()

        # Revert settings file (default prior to changing the settings file)
        self.currentSettingsController.writeSettingsFile()

        # Configure new settings (default settings + custom settings for this setup)
        self.settingsController.readSettingsFile()
        for settingsStage in settingCustomisation.keys():
            for settingsName, settingsValue in settingCustomisation.get(
                settingsStage
            ).items():
                self.settingsController.setSettingValue(
                    settingsStage, settingsName, settingsValue
                )
        self.settingsController.writeSettingsFile()

    def __setupTestFiles(
        self, modName: str, testFiles: dict[str, any]
    ) -> None:
        # Copy across all test files and populate test list file
        testDir = f"{self.modlistController.modFolderDir}/factorio-unit-test/temp"
        if os.path.exists(testDir):
            shutil.rmtree(testDir)
        os.makedirs(testDir)

        # TODO support wildcard test matching?

        for test in testFiles.keys():
            if test.startswith("common."):
                test = test[7:]  # Remove 'common.' prefix
                # Take from factorio-unit-test mod rather than the mod being tested
                shutil.copy(f"{self.modlistController.modFolderDir}/factorio-unit-test/unit-tests/{test}.lua", f"{testDir}/{test}.lua")
            else:
                shutil.copy(f"{self.modlistController.modFolderDir}/{modName}/unit-tests/{test}.lua", f"{testDir}/{test}.lua")

        # Write the test list file
        testListFileStr = "return {\n"
        for test in testFiles.keys():
            if test.startswith("common."):
                test = test[7:]  # Remove 'common.' prefix
            testListFileStr += f'  "{test}",\n'
        testListFileStr += "}\n"
        with open(f"{self.modlistController.modFolderDir}/factorio-unit-test/unit-test-list.lua", "w") as testListFile:
            testListFile.write(testListFileStr)

    def __executeUnitTests(self) -> bool:
        # Execute unit tests for the current test configuration
        self.factorioController.launchGame()
        testResult: bool = self.factorioController.executeUnitTests()
        self.factorioController.terminateGame()
        return testResult


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Factorio unit tests with various configurations."
    )
    parser.add_argument(
        "-f", "--factoriodir", type=str, help="Path to the Factorio user data directory"
    )
    parser.add_argument(
        "-i",
        "--installdir",
        type=str,
        help="Path to the Factorio installation directory",
    )
    parser.add_argument("-l", "--log", action="store_true", help="Log output to file")
    parser.add_argument(
        "-m", "--mod-directory", type=str, help="Path to the Factorio mods directory"
    )
    parser.add_argument("mod", type=str, help="The mod to test")

    args = parser.parse_args()

    factorioFolderDir: Optional[str] = (
        os.path.realpath(args.factoriodir.strip()) if args.factoriodir else None
    )
    factorioInstallDir: Optional[str] = (
        os.path.realpath(args.installdir.strip()) if args.installdir else None
    )
    factorioModDir: Optional[str] = (
        os.path.realpath(args.mod_directory.strip()) if args.mod_directory else None
    )
    logToFile: bool = args.log
    modToTest: str = args.mod.strip()


    testController = UnitTestController(
        updateMods=False,
        factorioInstallDir=factorioInstallDir,
        factorioFolderDir=factorioFolderDir,
        logToFile=logToFile,
        factorioModDir=factorioModDir,
    )
    
    configFile = testController.currentModlistController.modFolderDir + f"/{modToTest}/unit-test-config.jsonnet"
    testConfigurations: UnitTestConfiguration = UnitTestConfiguration(modToTest, configFile)

    testController.TestConfigurations(testConfigurations)
    testController.close()
