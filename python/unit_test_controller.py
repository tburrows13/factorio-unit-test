from __future__ import annotations
from typing import Optional
import os, sys, getopt
from pathlib import Path

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
        factorioPath: Optional[Path] = None,
        userDataDirectory: Optional[Path] = None,
        modDirectory: Optional[Path] = None,
        logToFile: bool = False,
    ):
        if not userDataDirectory:
            userDataDirectory = Path(os.getenv("APPDATA")) / "Factorio/"

        if not modDirectory:
            modDirectory = userDataDirectory / "mods"

        """
        if updateMods:
            self.__buildAngelsMods()
            self.__buildBobsMods()
        """

        # Backup the current mod config and mod settings
        self.currentModlistController = ModlistController(
            userDataDirectory, modDirectory
        )
        self.currentModlistController.readConfigurationFile()
        self.currentSettingsController = SettingsController(
            userDataDirectory, modDirectory
        )
        self.currentSettingsController.readSettingsFile()

        # Logger for unit test output
        self.logger = UnitTestLogger(logToFile)

        # New controllers for the unit tests
        self.modlistController = ModlistController(userDataDirectory, modDirectory)
        self.settingsController = SettingsController(userDataDirectory, modDirectory)
        self.factorioController = FactorioController(
            factorioPath, modDirectory, self.logger
        )

    def __del__(self):
        # Reset mod config and mod settings to the backed up values
        self.currentModlistController.disableMod("angelsdev-unit-test")
        self.currentModlistController.writeConfigurationFile()
        self.currentSettingsController.writeSettingsFile()

    def TestConfigurations(
        self,
        testConfigurations: UnitTestConfiguration,
        logSummary: bool = True,
    ) -> None:
        testResults: dict[str, bool] = dict()
        for configName, modList, settingCustomisation in testConfigurations:
            self.__logTestConfiguration(configName)
            self.__setupTestConfiguration(modList, settingCustomisation)
            testResults[configName] = self.__executeUnitTests()
        if logSummary:
            self.logger("Summary:", leading_newline=True)
            for testName, testResult in testResults.items():
                self.logger(f"[{'PASSED' if testResult else 'FAILED'}] {testName}")

    """
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
    """

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
        if "angelsdev-unit-test" not in modList:
            self.modlistController.enableMod("angelsdev-unit-test")
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

    def __executeUnitTests(self) -> bool:
        # Execute unit tests for the current test configuration
        self.factorioController.launchGame()
        testResult: bool = self.factorioController.executeUnitTests()
        self.factorioController.terminateGame()
        return testResult


"""
if __name__ == "__main__":
    factorioFolderDir: Optional[Path] = None
    factorioInstallDir: Optional[Path] = None
    factorioModDir: Optional[Path] = None
    logToFile: bool = False

    opts, args = getopt.getopt(
        sys.argv[1:], "f:i:l:m:", ["factoriodir=", "installdir=", "mod-directory="]
    )
    for opt, arg in opts:
        if opt in ("-f", "--factoriodir"):
            factorioFolderDir = Path(arg.strip()).expanduser().resolve()
        if opt in ("-i", "--installdir"):
            factorioInstallDir = Path(arg.strip()).expanduser().resolve()
        if opt in ("-l"):
            logToFile = True
        if opt in ("-m", "--mod-directory"):
            factorioModDir = Path(arg.strip()).expanduser().resolve()

    UnitTestController(
        updateMods=False,
        factorioInstallDir=factorioInstallDir,
        factorioFolderDir=factorioFolderDir,
        logToFile=logToFile,
        factorioModDir=factorioModDir,
    ).TestConfigurations(UnitTestConfiguration())
"""
