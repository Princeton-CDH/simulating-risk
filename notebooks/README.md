# Analysis Notebooks

Marimo notebooks for analysis of simulation batch run data. Notebooks are organized by simulation type:

- `evolv/` — Hawk/Dove with Evolving Risk-Attitudes
- `multi/` — Hawk/Dove with Multiple Risk-Attitudes

## Exporting to docs

Notebooks are exported as static HTML into `docs/analysis/`. Use `just` to export:

```sh
# export a single notebook
just docs-notebook notebooks/evolv/overview.py

# export all notebooks (and the app)
just docs
```

## Authoring conventions

New notebooks included in docs should set `html_head_file` and `app_title` in `marimo.App()`:

```python
app = marimo.App(
    width="medium",
    app_title="Topic - Hawk/Dove with Series Name",
    html_head_file="../docs_head.html",
)
```

- `html_head_file` injects the favicon and any shared head content from `notebooks/docs_head.html`
- `app_title` sets the browser tab title; follow the `{topic} - {series}` order (specific to general)
