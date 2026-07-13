import marimo as mo


def docs_header():
    """Site navigation for notebooks included in exported documentation.
    Include at the top of notebooks and hide code.

    ```python
        from simulatingrisk.doc_utils import docs_header

        docs_header()
    ```
    """
    # nested links do not work well in static html export (displays under the code),
    # so only include top-level link
    return mo.nav_menu(
        {
            "/simulating-risk/": "Home",
            "/simulating-risk/app/": "Simulation",
            "/simulating-risk/analysis/": "Analysis",
        }
    )
