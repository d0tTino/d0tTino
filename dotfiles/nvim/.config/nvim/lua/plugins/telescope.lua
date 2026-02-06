return {
    {
        "nvim-telescope/telescope.nvim",
        cmd = "Telescope",
        dependencies = {
            "nvim-lua/plenary.nvim",
        },
        opts = {
            defaults = {
                layout_strategy = "horizontal",
                sorting_strategy = "ascending",
            },
        },
    },
}
