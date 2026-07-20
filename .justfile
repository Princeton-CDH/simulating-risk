# justfile for building and serving notebooks as local html
set default-list := true

# export a single marimo notebook to static html in docs/analysis/
docs-notebook PATH:
    #!/usr/bin/env bash
    echo "Exporting notebook {{PATH}} to html in docs/analysis/"
    # get base filename without the .py extension
    output_path=$(basename {{PATH}} ".py")
    # get directory path relative to notebooks/ directory, which is mirrored in output
    # use basename and dirname together to get the notebook subirectory name
    sub_dir=$(basename `dirname {{PATH}}`)
    echo "... uv run marimo export html {{ PATH }} -o docs/analysis/$sub_dir/$output_path.html --force"
    uv run marimo export html {{ PATH }} -o docs/analysis/$sub_dir/$output_path.html --force

# Export marimo app and all analysis notebooks to html docs (SLOW)
docs:
    @echo "Exporting app ui to html-wasm in docs/app/"
    uv run marimo --quiet export html-wasm simulatingrisk/app.py -o docs/app/ --mode run --no-sandbox --force
    @cp notebooks/docs_head.html docs/
    @sed -i '' 's|docs/docs_head.html|docs_head.html|g' docs/app/index.html
    @echo "\n🔺 multiple risk attitudes"
    @just docs-notebook notebooks/multi/overview.py
    @just docs-notebook notebooks/multi/overview.py
    @just docs-notebook notebooks/multi/hawk-play-frequency.py
    @just docs-notebook notebooks/multi/payoff_significance.py
    @echo "\n🔺 evolving risk attitudes"
    @just docs-notebook notebooks/evolv/overview.py
    @just docs-notebook notebooks/evolv/population-category.py
    @just docs-notebook notebooks/evolv/param-significance.py



# serve documentation locally for development and testing
serve-docs:
    #!/usr/bin/env bash
    tmpdir=$(mktemp -d -t simrisk_docs_)
    trap 'rm -rf "$tmpdir"' EXIT
    ln -s "$PWD/docs" "$tmpdir/simulating-risk"
    echo "Serving at http://localhost:8000/simulating-risk/"
    python -m http.server 8000 --directory "$tmpdir"
