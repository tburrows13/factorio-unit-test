import os, sys, getopt
import json
from typing import Optional
from pathlib import Path


class ModlistController:
    # References:
    #   https://wiki.factorio.com/Mod_settings_file_format
    #   https://wiki.factorio.com/Property_tree

    modDirectory: Path
    modlist: Optional[dict]

    def __init__(
        self,
        userDataDirectory: Optional[Path] = None,
        modDirectory: Optional[Path] = None,
    ):
        if modDirectory:
            self.modDirectory = modDirectory
        elif userDataDirectory:
            self.modDirectory = userDataDirectory / "mods"
        else:
            self.modDirectory = Path(os.getenv("APPDATA")) / "Factorio" / "mods"

    def readConfigurationFile(self, filename: str = "mod-list.json") -> None:
        filepath = self.modDirectory / filename
        with filepath.open("r") as modlistFile:
            self.modlist = json.load(modlistFile).get("mods")

    def writeConfigurationFile(self, filename: str = "mod-list.json") -> None:
        filepath = self.modDirectory / filename
        with filepath.open("w") as modlistFile:
            json.dump({"mods": self.modlist}, modlistFile, indent=2)

    def disableAllMods(self) -> None:
        for mod in self.modlist:
            mod["enabled"] = mod["name"] == "base"

    def disableMod(self, modname: str) -> None:
        if modname == "base":
            return
        for mod in self.modlist:
            if mod["name"] == modname:
                mod["enabled"] = modname == "base"  # base mod cannot be disabled
                return
        self.modlist.append({"name": modname, "enabled": modname == "base"})

    def enableMod(self, modname: str) -> None:
        for mod in self.modlist:
            if mod["name"] == modname:
                mod["enabled"] = True
                return
        self.modlist.append({"name": modname, "enabled": True})


if __name__ == "__main__":
    factorioFolderDir: Optional[Path] = None
    factorioModDir: Optional[Path] = None

    opts, args = getopt.getopt(sys.argv[1:], "f:m:", ["factoriodir=", "mod-directory="])
    for opt, arg in opts:
        if opt in ("-f", "--factoriodir"):
            factorioFolderDir = Path(arg.strip()).expanduser().resolve()
        if opt in ("-m", "--mod-directory"):
            factorioModDir = Path(arg.strip()).expanduser().resolve()

    mc = ModlistController(factorioFolderDir, factorioModDir)
    mc.readConfigurationFile()
    mc.disableAllMods()
    mc.enableMod("angelsinfiniteores")
    mc.enableMod("angelsrefining")
    mc.enableMod("angelsrefininggraphics")
    mc.enableMod("angelspetrochem")
    mc.enableMod("angelspetrochemgraphics")
    mc.enableMod("angelssmelting")
    mc.enableMod("angelssmeltinggraphics")
    mc.enableMod("angelsbioprocessing")
    mc.enableMod("angelsbioprocessinggraphics")
    mc.enableMod("angelsindustries")
    mc.enableMod("angelsindustriesgraphics")
    mc.enableMod("angelsexploration")
    mc.enableMod("angelsexplorationgraphics")
    mc.writeConfigurationFile("mod-list-dupe.json")
