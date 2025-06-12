from __future__ import annotations
from typing import Optional, Any
import os, sys, shutil, getopt, re
from pathlib import Path

# from mod_builder import ModBuilder
# from mod_downloader import ModDownloader
from .modlist_controller import ModlistController
from .settings_controller import SettingsController
from .factorio_controller import FactorioController
from .unit_test_configuration import UnitTestConfiguration
from .unit_test_logger import UnitTestLogger


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
            if appdataPath := os.getenv("APPDATA"):
                userDataDirectory = (
                    Path(appdataPath).expanduser().resolve() / "Factorio"
                )
            else:
                raise FileNotFoundError("Could not find user data directory.")

        if not modDirectory:
            modDirectory = userDataDirectory / "mods"
            self.modDirectory = modDirectory

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

    def __setupTestFiles(self, modName: str, testFiles: dict[str, Any]) -> None:
        # Copy across all test files and populate test list file
        modDirectory = self.modlistController.modDirectory
        testDir = modDirectory / "factorio-unit-test/temp"
        if testDir.exists():
            shutil.rmtree(testDir)
        testDir.mkdir()

        # Build up test list file as we go
        testListFileStr = "return {\n"

        for test in testFiles.keys():
            if test.startswith("common."):
                test = test[7:]  # Remove 'common.' prefix
                # Take from factorio-unit-test mod rather than the mod being tested
                file_paths = sorted(
                    (modDirectory / "factorio-unit-test" / "unit-tests").glob(test + ".lua")
                )
                if not file_paths:
                    self.logger(f"No matching test files found for common.{test}")
                for file_path in file_paths:
                    dest_path = testDir / file_path.name
                    shutil.copy(file_path, dest_path)
                    self.__applyMacros(dest_path)
                    testListFileStr += f'  "{file_path.stem}",\n'
            else:
                file_paths = sorted((modDirectory / modName / "unit-tests").glob(test + ".lua"))
                if not file_paths:
                    self.logger(f"No matching test files found for {test}")
                for file_path in file_paths:
                    dest_path = testDir / file_path.name
                    shutil.copy(file_path, dest_path)
                    self.__applyMacros(dest_path)
                    testListFileStr += f'  "{file_path.stem}",\n'

        testListFileStr += "}\n"
        with (modDirectory / "factorio-unit-test" / "temp-test-list.lua").open(
            "w"
        ) as tempTestListFile:
            tempTestListFile.write(testListFileStr)

    def __executeUnitTests(self) -> bool:
        # Execute unit tests for the current test configuration
        self.factorioController.launchGame()
        testResult: bool = self.factorioController.executeUnitTests()
        self.factorioController.terminateGame()
        return testResult

    def __applyMacros(self, filePath: Path) -> None:
        """Apply macro transformations to a Lua file."""
        with filePath.open('r') as file:
            content = file.read()
        
        # Transform ASSERT(expression, log-message) to if expression then LOG(log-message) return FAIL end
        # Use regex to match ASSERT calls with proper parentheses handling
        def replace_assert(match):
            # Extract the expression and log message
            inner_content = match.group(1)
            
            # Find the comma that separates expression from log message
            # We need to handle nested parentheses properly
            paren_count = 0
            comma_pos = -1
            for i, char in enumerate(inner_content):
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                elif char == ',' and paren_count == 0:
                    comma_pos = i
                    break
            
            if comma_pos == -1:
                # No comma found, malformed ASSERT
                return match.group(0)
            
            expression = inner_content[:comma_pos].strip()
            log_message = inner_content[comma_pos + 1:].strip()
            
            return f"if not ({expression}) then LOG({log_message}) return FAIL end"
        
        # Apply the transformation
        pattern = r'ASSERT\(([^)]*(?:\([^)]*\)[^)]*)*)\)'
        content = re.sub(pattern, replace_assert, content)
        
        # Write the modified content back to the file
        with filePath.open('w') as file:
            file.write(content)


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
