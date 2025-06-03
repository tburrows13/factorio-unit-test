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
    }
}