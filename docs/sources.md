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

## Enriching Source Information

`scripts/enrich_sources.py` augments `sources.json` with details such as
GitHub star counts and a guessed API type. Run it whenever you want to refresh
this metadata locally:

```bash
python scripts/enrich_sources.py
python scripts/generate_sources_md.py
```

Both the JSON file and the generated Markdown should be committed after running
the enrichment script.

## Scheduled Enrichment Workflow

The `.github/workflows/enrich-sources.yml` workflow performs this enrichment
automatically every Sunday at 00:00&nbsp;UTC. It installs Python, runs the
enrichment script with the repository's `GITHUB_TOKEN`, and commits any
resulting updates to `sources.json` and `docs/awesome-sources.md`. You can also
trigger the workflow manually from the Actions tab.
