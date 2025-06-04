from __future__ import annotations
from typing import Iterable, Optional
from pathlib import Path
import json
import _jsonnet

SettingsType = dict[str, dict[str, bool]]
ModListType = list[str]
TestListType = dict[str, dict]
ConfigurationType = dict[str, SettingsType | ModListType]


class UnitTestConfiguration:
    """An iterable object containing all test configurations."""

    def __init__(self, modName: str, configFile: Optional[Path]):
        self.modName: str = modName
        self.default_settings: SettingsType = {}
        self.configurations: dict[str, ConfigurationType] = {}
        self.tests: TestListType = {}

        # Read config json and populate configurations
        if configFile is not None:
            configDataStr = _jsonnet.evaluate_file(configFile)
            configData = json.loads(configDataStr)
            self.default_settings = configData.get("default_settings", {})
            self.configurations = configData.get("configurations", [])
            self.tests = configData.get("tests", {})

            # Apply default settings to each configuration
            for configName, configData in self.configurations.items():
                if "settings" not in configData:
                    configData["settings"] = {}
                for settingStage, stageSettings in self.default_settings.items():
                    if settingStage not in configData["settings"]:
                        configData["settings"][settingStage] = {}
                    for settingName, settingDefaultValue in stageSettings.items():
                        if settingName not in configData["settings"][settingStage]:
                            configData["settings"][settingStage][
                                settingName
                            ] = settingDefaultValue

    def __iter__(
        self,
    ) -> Iterable[tuple[str, ConfigurationType]]:
        return iter(self.configurations.items())

    """
    def addDefaultSetting(
        self,
        settingStage: str,
        settingName: str,
        settingDefaultValue: bool,
    ) -> None:
        if settingStage not in self.default_settings.keys():
            self.default_settings[settingStage] = {}
        self.default_settings[settingStage][settingName] = settingDefaultValue

    def addConfiguration(
        self,
        configName: str,
        modList: list[str],
        settingCustomisation: dict[str, dict[str, bool]],
    ) -> None:
        for settingStage, stageSettings in self.default_settings.items():
            if settingStage not in settingCustomisation.keys():
                settingCustomisation[settingStage] = {}
            for settingName, settingDefaultValue in stageSettings.items():
                if settingName not in settingCustomisation[settingStage].keys():
                    settingCustomisation[settingStage][
                        settingName
                    ] = settingDefaultValue
        self.configurations[configName] = {
            "settings": settingCustomisation,
            "mods": modList,
        }
    """
