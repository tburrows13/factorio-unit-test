{
    defaultSettings:
    {
        startup: {
            "angels-hide-converter": true,
            "angels-enable-acids": true,
        },
    },
    configurations:
    {
        "Special vanilla (light)":
        {
            settings: {
                startup: {
                    "angels-hide-converter": false,
                    "angels-enable-acids": false,
                },
            },
            mods: [
                "angelspetrochem",
                "angelssmelting",
                "angelssmelting-extended",
                "angelssmelting-extended-vanilla",
            ],
        },
        "Special vanilla (regular)":
        {
            settings: {
                startup: {
                    "angels-hide-converter": false,
                    "angels-enable-acids": false,
                },
            },
            mods: [
                "angelspetrochem",
                "angelssmelting",
                "angelssmelting-extended",
                "angelssmelting-extended-vanilla",
                "angelsaddons-storage",
            ],
        },
    },
    tests:
    {
        "test-science-packs": {},
        "common.unit-test-001": {},
        "common.unit-test-01*": {},  // Can use wildcard patterns: https://docs.python.org/3/library/pathlib.html#pathlib-pattern-language
    }
}