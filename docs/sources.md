# Managing Sources

The project tracks useful links in `metadata/sources.json`. A small script
converts this structured list into the human readable
`docs/awesome-sources.md` file:

```bash
python scripts/generate_sources_md.py
```

A GitHub Action defined in `.github/workflows/sources.yml` runs whenever the
JSON file changes. It validates and enriches the data before regenerating the
Markdown page. If the newly generated file differs from the version in the
repository, the action commits the update to the pull request or fails the
workflow.

Run the script locally and commit the updated Markdown whenever you add or
modify entries in `sources.json`.
