"""Regression checks for unified OpenAPI documentation."""

from main import OPENAPI_REQUIRED_PREFIXES, app


def test_unified_openapi_includes_all_required_service_prefixes() -> None:
    schema = app.openapi()
    paths = set(schema.get("paths", {}).keys())

    missing_prefixes = [
        prefix
        for prefix in OPENAPI_REQUIRED_PREFIXES
        if not any(path.startswith(prefix) for path in paths)
    ]

    assert not missing_prefixes, (
        "Unified OpenAPI docs are missing service endpoints for prefixes: "
        + ", ".join(sorted(missing_prefixes))
    )


