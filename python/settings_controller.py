from typing import Union, Optional, BinaryIO
import os, sys, getopt
import struct
from pathlib import Path
from enum import IntEnum


class PTreeType(IntEnum):
    NONE = 0
    BOOL = 1
    NUMBER = 2
    STRING = 3
    LIST = 4
    DICTIONARY = 5
    SIGNED_LONG = 6
    UNSIGNED_LONG = 7


class SettingsFileReader:
    file: BinaryIO

    def __init__(self, file):
        self.file = file

    def readBool(self) -> bool:
        return bool.from_bytes(self.file.read(1), byteorder="little")

    def readByte(self) -> int:
        return int.from_bytes(self.file.read(1), byteorder="little")

    def readUnsignedShort(self) -> int:
        return int.from_bytes(self.file.read(2), byteorder="little")

    def readUnsignedInteger(self, spaceOptimised: bool = False) -> int:
        if not spaceOptimised:
            return int.from_bytes(self.file.read(4), byteorder="little")

        value = self.readByte()
        return value if value < 255 else self.readUnsignedInteger(spaceOptimised=False)

    def readSignedLong(self) -> int:
        return int.from_bytes(self.file.read(8), byteorder="little", signed=True)

    def readUnsignedLong(self) -> int:
        return int.from_bytes(self.file.read(8), byteorder="little")

    def readNumber(self) -> float:
        # IEEE 754 double-precision binary floating-point format
        return struct.unpack("<d", self.file.read(8))[0]

    def readString(self) -> str:
        if self.readBool():
            return ""
        return self.file.read(self.readUnsignedInteger(spaceOptimised=True)).decode(
            "utf-8"
        )

    def readDictionary(self, dictName: str = "") -> Union[bool, float, str, dict]:
        treeType = self.readByte()
        treeBool = self.readBool()
        if treeType == PTreeType.NONE:
            raise NotImplementedError
        elif treeType == PTreeType.BOOL:
            return self.readBool()
        elif treeType == PTreeType.NUMBER:
            return self.readNumber()
        elif treeType == PTreeType.STRING:
            return self.readString()
        elif treeType == PTreeType.LIST:
            raise NotImplementedError
        elif treeType == PTreeType.DICTIONARY:
            treeVal = dict()
            dictSize = self.readUnsignedInteger()
            for dictIndex in range(dictSize):
                dictKey = self.readString()
                treeVal[dictIndex] = [dictKey, self.readDictionary()]
            return treeVal
        elif treeType == PTreeType.SIGNED_LONG:
            return self.readSignedLong()
        elif treeType == PTreeType.UNSIGNED_LONG:
            return self.readUnsignedLong()
        else:
            raise ValueError(f"Type '{treeType}' is invalid for dict {dictName}.")


class SettingsFileWriter:
    file: BinaryIO

    def __init__(self, file):
        self.file = file

    def writeBool(self, value: bool) -> None:
        self.file.write(value.to_bytes(1, "little"))

    def writeByte(self, value: int) -> None:
        self.file.write(value.to_bytes(1, "little"))

    def writeUnsignedShort(self, value: int) -> None:
        self.file.write(value.to_bytes(2, "little"))

    def writeUnsignedInteger(self, value: int, spaceOptimised: bool = False) -> None:
        if spaceOptimised:
            self.writeByte(min(value, 255))
            if value >= 255:
                self.writeUnsignedInteger(value, spaceOptimised=False)
        else:
            self.file.write(value.to_bytes(4, "little"))

    def writeSignedLong(self, value: int) -> None:
        self.file.write(value.to_bytes(8, "little", signed=True))

    def writeUnsignedLong(self, value: int) -> None:
        self.file.write(value.to_bytes(8, "little"))

    def writeNumber(self, value: float) -> None:
        # IEEE 754 double-precision binary floating-point format
        self.file.write(struct.pack("<d", value))

    def writeString(self, value: str) -> None:
        empty = value == ""
        self.writeBool(False)  # not refering to nullptr
        self.writeUnsignedInteger(len(value), spaceOptimised=True)
        if not empty:
            self.file.write(value.encode("utf-8"))

    def writeDictionary(self, value: dict) -> None:
        self.writePropertyType(PTreeType.DICTIONARY)
        dictSize = len(value.keys())
        self.writeUnsignedInteger(dictSize)
        for dictIndex in range(dictSize):
            dictKey, dictValue = value.get(dictIndex)
            self.writeString(dictKey)
            if type(dictValue) is None:
                raise NotImplementedError
            elif type(dictValue) is bool:
                self.writePropertyType(PTreeType.BOOL)
                self.writeBool(dictValue)
            elif type(dictValue) is float:
                self.writePropertyType(PTreeType.NUMBER)
                self.writeNumber(dictValue)
            elif type(dictValue) is str:
                self.writePropertyType(PTreeType.STRING)
                self.writeString(dictValue)
            elif type(dictValue) is list:
                raise NotImplementedError
            elif type(dictValue) is dict:
                raise NotImplementedError
            elif type(dictValue) is int:
                if dictValue < 0:
                    self.writePropertyType(PTreeType.SIGNED_LONG)
                    self.writeSignedLong(dictValue)
                else:
                    self.writePropertyType(PTreeType.UNSIGNED_LONG)
                    self.writeUnsignedLong(dictValue)
            else:
                raise ValueError(
                    f"Type '{type(dictValue).__name__}' is invalid for dict {dictKey}."
                )

    def writeVersion(self, version: list) -> None:
        for v in range(4):
            self.writeUnsignedShort(version[v])

    def writePropertyType(self, type: PTreeType) -> None:
        self.writeByte(type)
        self.writeBool(False)


class SettingsController:
    # References:
    #   https://wiki.factorio.com/Mod_settings_file_format
    #   https://wiki.factorio.com/Property_tree

    modDirectory: Path
    settings: Optional[dict]

    def __init__(
        self,
        userDataDirectory: Optional[Path] = None,
        modDirectory: Optional[Path] = None,
    ):
        if modDirectory:
            self.modDirectory: Path = modDirectory
        elif userDataDirectory:
            self.modDirectory = userDataDirectory / "mods"
        else:
            self.modDirectory = Path(os.getenv("APPDATA")) / "Factorio" / "mods"

    def readSettingsFile(self, filename: str = "mod-settings.dat") -> None:
        filepath = self.modDirectory / filename
        with filepath.open("rb") as modSettingsFile:
            modSettings = SettingsFileReader(modSettingsFile)
            self.settings = dict()
            # Version of the mod
            self.settings["version"] = [
                modSettings.readUnsignedShort() for _ in range(4)
            ]
            _ = modSettings.readBool()
            # print(f"Loading {filename} version {'.'.join([str(v) for v in self.settings.get('version')])}")

            # Property tree
            propertyTreeType = modSettings.readByte()
            propertyTreeBool = modSettings.readBool()
            assert propertyTreeType == 5, "Invalid settings structure type detected!"
            settingCount = modSettings.readUnsignedInteger()
            assert settingCount == 3, "Invalid amount of setting stages!"
            for settingIndex in range(settingCount):
                settingStageName = modSettings.readString()
                # print(f"\tReading {settingStageName} settings")
                self.settings[settingStageName] = dict()

                stagePropertyTreeType = modSettings.readByte()
                stagePropertyTreeBool = modSettings.readBool()
                assert (
                    stagePropertyTreeType == 5
                ), "Invalid settings stage structure type detected!"
                stageSettingCount = modSettings.readUnsignedInteger()
                for stageSettingIndex in range(stageSettingCount):
                    stageSettingIndexName = modSettings.readString()
                    self.settings[settingStageName][stageSettingIndex] = [
                        stageSettingIndexName,
                        modSettings.readDictionary(stageSettingIndexName),
                    ]

    def writeSettingsFile(self, filename: str = "mod-settings.dat") -> None:
        filepath = self.modDirectory / filename
        filepath.unlink(missing_ok=True)  # Delete current file if exists
        with filepath.open("wb") as modSettingsFile:
            modSettings = SettingsFileWriter(modSettingsFile)

            # Version of the mod
            # print(f"Writing {filename} version {'.'.join([str(v) for v in self.settings.get('version')])}")
            modSettings.writeVersion(self.settings.get("version"))
            modSettings.writeBool(False)

            # Property tree
            modSettings.writePropertyType(PTreeType.DICTIONARY)

            modSettingsStages = ["startup", "runtime-global", "runtime-per-user"]
            modSettings.writeUnsignedInteger(len(modSettingsStages))
            for modSettingsStage in modSettingsStages:
                # print(f"\tWriting {modSettingsStage} settings")
                modSettings.writeString(modSettingsStage)
                modSettings.writePropertyType(PTreeType.DICTIONARY)
                stageSettingCount = len(self.settings[modSettingsStage].keys())
                modSettings.writeUnsignedInteger(stageSettingCount)
                for stageSettingIndex in range(stageSettingCount):
                    stageSettingKey, stageSettingValue = self.settings[
                        modSettingsStage
                    ].get(stageSettingIndex)
                    modSettings.writeString(stageSettingKey)
                    modSettings.writeDictionary(stageSettingValue)

    def setSettingValue(
        self,
        settingType: str,
        settingName: str,
        settingValue: Union[bool, float, str, dict],
    ) -> None:
        # Check all settings if the setting already exists
        validSettingType = False
        for modSettingsStage in ["startup", "runtime-global", "runtime-per-user"]:
            for modSettingIndex, modSetting in self.settings[modSettingsStage].items():
                dictKey, dictValue = modSetting
                if settingName == dictKey:
                    assert (
                        modSettingsStage == settingType
                    ), f"Error: Setting {settingName} is not a {settingType} setting."
                    assert type(settingValue) is type(
                        dictValue[0][1]
                    ), f"Error: Setting {settingName} should be of type {type(dictValue[0][1]).__name__}"
                    dictValue[0][1] = settingValue
                    return

            validSettingType = validSettingType or (modSettingsStage == settingType)

        # Setting does not exist yet at this point
        assert validSettingType, f"Error: {settingType} is not a valid setting stage."
        modSettingStage = self.settings[settingType]
        modSettingStage[len(modSettingStage.keys())] = [
            settingName,
            {0: ["value", settingValue]},
        ]


if __name__ == "__main__":
    factorioFolderDir: Optional[Path] = None
    factorioModDir: Optional[Path] = None

    opts, args = getopt.getopt(sys.argv[1:], "f:m:", ["factoriodir=", "mod-directory="])
    for opt, arg in opts:
        if opt in ("-f", "--factoriodir"):
            factorioFolderDir = Path(arg.strip()).expanduser().resolve()
        if opt in ("-m", "--mod-directory"):
            factorioModDir = Path(arg.strip()).expanduser().resolve()

    sc = SettingsController(factorioFolderDir, factorioModDir)
    sc.readSettingsFile()
    sc.setSettingValue("startup", "angels-enable-industries", True)  # angels override
    sc.writeSettingsFile("mod-settings-dupe.dat")
