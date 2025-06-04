from __future__ import annotations
from typing import Optional, TextIO

import os
from datetime import datetime
from pathlib import Path


class UnitTestLogger:
    logToFile: bool
    logFilePath: Path
    logFileHandler: Optional[TextIO]

    def __init__(self, logToFile: bool = False):
        self.logToFile = logToFile
        log_dir = Path(__file__).parent.parent / "log"
        log_filename = f"unit_test_{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        self.logFilePath = log_dir / log_filename
        self.logFileHandler = None

        if self.logToFile:
            self.logFilePath.parent.mkdir(parents=True, exist_ok=True)
            assert not self.logFilePath.exists(), "Log file already exists!"
            self.logFileHandler = self.logFilePath.open(mode="x")

    def __del__(self):
        if self.logToFile and self.logFileHandler:
            self.logFileHandler.close()
            self.logFileHandler = None
            self.logToFile = False

    def __call__(self, msg: str, leading_newline: bool = False) -> None:
        lead = "\n" if leading_newline else ""
        print(f"{lead}factorio-unit-test: {msg}")
        if self.logToFile and self.logFileHandler:
            print(
                f"{lead}factorio-unit-test: {msg}",
                file=self.logFileHandler,
                flush=True,
            )


if __name__ == "__main__":
    utl = UnitTestLogger(True)
    utl("test")
