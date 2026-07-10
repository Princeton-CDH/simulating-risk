# justfile for building and serving notebooks as local html
set default-list := true

# TODO: may need base url option with exports to run properly on github pages

# Export marimo app and analysis notebooks to html docs
docs:
    @echo "Exporting app ui to html-wasm in docs/sim/"
    uv run marimo --quiet export html-wasm simulatingrisk/app.py -o docs/sim/ --mode run --no-sandbox --force

#uv run marimo export html notebooks/evolv/convergence.py -o docs/analysis/evolve/convergence.html

# serve documentation locally for dev/
serve-docs:
    @echo "Serving docs/ at http://localhost:8000/"
    python -m http.server --directory docs/
