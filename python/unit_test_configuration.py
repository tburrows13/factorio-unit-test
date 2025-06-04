from __future__ import annotations
from typing import Iterable, Optional
import json
import _jsonnet

SettingsType = dict[str, dict[str, bool]]
ModListType = list[str]
ConfigurationType = dict[str, SettingsType | ModListType]


class UnitTestConfiguration:
    """An iterable object containing all test configurations."""

    def __init__(self, configFile: Optional[Path]):
        self.default_settings: SettingsType = {}
        self.configurations: dict[str, ConfigurationType] = {}

        # Read config json and populate configurations
        if configFile is not None:
            configDataStr = _jsonnet.evaluate_file(configFile)
            configData = json.loads(configDataStr)
            self.default_settings = configData.get("default_settings", {})
            self.configurations = configData.get("configurations", [])

    def __iter__(
        self,
    ) -> Iterable[tuple[str, ConfigurationType]]:
        return iter(self.configurations.items())

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
