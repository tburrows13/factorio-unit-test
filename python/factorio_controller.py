from typing import Callable, Union, Optional, Iterable
import os, subprocess
from shlex import shlex
import json
import re
import time
from pathlib import Path


class FactorioController:
    factorioPath: Path
    log: Callable[[str], None]
    factorioArgs: list[str]
    factorioProcess: Optional[subprocess.Popen]

    def __init__(
        self,
        factorioPath: Optional[Path] = None,
        modDirectory: Optional[Path] = None,
        log: Optional[Callable[[str], None]] = None,
    ):
        if factorioPath is None:
            self.factorioPath = (
                Path(self.__retrieveSteamGameInstallLocation(427520))
                / "bin/x64/factorio.exe"
            )
        else:
            self.factorioPath = factorioPath
        if log is None:
            self.log = lambda msg: print(f"factorio-unit-test: {msg}")
        else:
            self.log = log
        self.factorioArgs = self.__createFactorioArgs(modDirectory)
        self.factorioProcess = None

    def launchGame(self) -> None:
        # https://developer.valvesoftware.com/wiki/Command_Line_Options#Steam_.28Windows.29
        self.log(f"Launching {self.factorioPath.name}")
        try:
            # Prevents Steam from requiring user confirmation of launch
            env = os.environ.copy()
            env['SteamAppId'] = '427520'
            
            self.factorioProcess = subprocess.Popen(
                executable=self.factorioPath,
                args=self.factorioArgs,
                cwd=self.factorioPath.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
        except FileNotFoundError as fnfe:
            print(f"The system could not find {self.factorioPath}.")
            raise fnfe

    def terminateGame(self) -> None:
        if self.factorioProcess is None:
            self.log("No factorio process to terminate.")
            return

        if self.factorioProcess.poll() is None:
            self.factorioProcess.terminate()
            self.log(f"Closing {self.factorioPath.name}")
            time.sleep(3)  # Allow the game to terminate fully
        else:
            self.log(f"{self.factorioPath.name} terminated unexpectedly...")
        self.factorioProcess = None

    def getGameOutput(self) -> Iterable[Union[str, bool]]:
        if self.factorioProcess is None:
            raise RuntimeError(
                "Factorio process is not running. Please launch the game first."
            )

        for stdoutLine in iter(self.factorioProcess.stdout.readline, ""):
            lineData = stdoutLine.strip().decode("utf-8")
            if lineData == "":
                yield self.factorioProcess.poll() is None
            else:
                yield lineData
        self.factorioProcess.stdout.close()
        return_code = self.factorioProcess.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, self.factorioPath)
        yield False  # App terminated

    def executeUnitTests(self) -> bool:
        # This does not actually execute anything, it waits till the mod signals the tests are finished while logging all unit test results
        for line in self.getGameOutput():
            if type(line) is str:
                if re.fullmatch(r"factorio\-unit\-test: .*", line):
                    self.log(line[20:])
                    if re.fullmatch(r"factorio\-unit\-test: Finished testing!.*", line):
                        return (
                            True
                            if re.fullmatch(r".* All unit tests passed!", line)
                            else False
                        )
                elif re.fullmatch(
                    r" *[0-9]+\.[0-9]{3} Error ModManager\.cpp\:[0-9]+\:.*", line
                ):
                    self.log(
                        line[
                            re.match(
                                r" *[0-9]+\.[0-9]{3} Error ModManager\.cpp\:[0-9]+\: *",
                                line,
                            ).regs[0][1] :
                        ]
                    )
                    return False  # Error during launch launch
            elif type(line) is bool and line is False:
                return False  # Terminated factorio
        return False  # unexpected end

    def __retrieveSteamGameInstallLocation(self, steamGameID: int) -> str:
        # Find install location of steam itself
        # TODO make platform-agnostic and use pathlib
        steamApp = subprocess.run(
            ["reg", "query", "HKCU\Software\Valve\Steam", "/v", "SteamExe"],
            stdout=subprocess.PIPE,
        ).stdout.decode("utf-8")
        steamApp = [
            entry
            for line in steamApp.split("\r\n")
            for entry in line.split("    ")
            if os.path.exists(entry)
            and os.access(entry, os.F_OK)
            and os.access(entry, os.X_OK)
        ]
        if len(steamApp) == 0:
            raise ValueError("Could not find a suitable steam installation")
        steamDir = os.path.dirname(steamApp[0])

        # Find install location of steam libraries
        def vdf2json(stream):
            # Code based on https://gist.github.com/ynsta/7221512c583fbfbafe6d#file-vdf2json-py-L5-L41
            def _istr(ident, string):
                return (ident * "  ") + string

            jbuf = "{\n"
            lex = shlex(stream)
            indent = 1

            while True:
                tok = lex.get_token()
                if not tok:
                    return json.loads(jbuf + "}\n")
                if tok == "}":
                    indent -= 1
                    jbuf += _istr(indent, "}")
                    ntok = lex.get_token()
                    lex.push_token(ntok)
                    if ntok and ntok != "}":
                        jbuf += ","
                    jbuf += "\n"
                else:
                    ntok = lex.get_token()
                    if ntok == "{":
                        jbuf += _istr(indent, tok + ": {\n")
                        indent += 1
                    else:
                        jbuf += _istr(indent, tok + ": " + ntok)
                        ntok = lex.get_token()
                        lex.push_token(ntok)
                        if ntok != "}":
                            jbuf += ","
                        jbuf += "\n"

        steamLibs = None
        with open(f"{steamDir}/steamapps/libraryfolders.vdf") as steamLibsFile:
            steamLibs = vdf2json(steamLibsFile.read())
        steamLibs = [
            v
            for k, v in steamLibs.get("LibraryFolders").items()
            if re.fullmatch(r"\d+", k)
        ]

        # Find in which lib the game is installed
        steamGameManifestLocation = None
        for steamLib in steamLibs:
            steamGameManifestLocation = (
                f"{steamLib}/steamapps/appmanifest_{steamGameID}.acf"
            )
            if os.path.isfile(steamGameManifestLocation):
                break
        if steamGameManifestLocation is None:
            raise ValueError("Could not find install location.")

        # Find the install directory for the game
        steamGameManifest = None
        with open(steamGameManifestLocation) as steamGameManifestFile:
            steamGameManifest = vdf2json(steamGameManifestFile.read())
        steamGameName = steamGameManifest.get("AppState").get("name")
        steamGameFolder = f"{steamLib}/steamapps/common/{steamGameName}"

        # Make sure it has an appropriate steam_appid.txt file
        steamAppIDLocation = f"{steamGameFolder}/bin/x64/steam_appid.txt"
        if not os.path.exists(steamAppIDLocation):
            with open(steamAppIDLocation, "w") as steamAppIDFile:
                steamAppIDFile.write(f"{steamGameID}")

        return steamGameFolder

    def __createFactorioArgs(self, modDirectory: Optional[Path] = None) -> list:
        def convert_to_arglist(arg: str) -> list:
            return arg.split(" ")

        args = []  # https://wiki.factorio.com/Command_line_parameters
        args.append(
            str(self.factorioPath)
        )  # because factorio expects the exe as first arg...
        # args.extend(convert_to_arglist("--verbose"))
        args.extend(convert_to_arglist("--load-scenario base/freeplay"))
        if modDirectory is not None:
            args.append("--mod-directory")
            args.append(str(modDirectory))

        return args


if __name__ == "__main__":
    fc = FactorioController()
    fc.launchGame()
    fc.executeUnitTests()
    fc.terminateGame()
