# justfile for building and serving notebooks as local html
set default-list := true

# TODO: may need base url option with exports to run properly on github pages

# Export marimo app and analysis notebooks to html docs
docs:
    @echo "Exporting app ui to html-wasm in docs/app/"
    uv run marimo --quiet export html-wasm simulatingrisk/app.py -o docs/app/ --mode run --no-sandbox --force
    @echo "Exporting analysis notebooks to html in docs/analysis/"
    uv run marimo export html notebooks/multi/overview.py -o docs/analysis/multi/overview.html --force

#uv run marimo export html notebooks/evolv/convergence.py -o docs/analysis/evolve/convergence.html

# serve documentation locally for development and testing
serve-docs:
    #!/usr/bin/env bash
    tmpdir=$(mktemp -d -t simrisk_docs_)
    trap 'rm -rf "$tmpdir"' EXIT
    ln -s "$PWD/docs" "$tmpdir/simulating-risk"
    echo "Serving at http://localhost:8000/simulating-risk/"
    python -m http.server 8000 --directory "$tmpdir"
