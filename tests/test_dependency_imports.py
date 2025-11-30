import importlib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _module_path(module) -> Path:
    module_file = getattr(module, "__file__", None)
    if module_file:
        return Path(module_file).resolve()
    module_paths = getattr(module, "__path__", None)
    if module_paths:
        return Path(list(module_paths)[0]).resolve()
    raise AssertionError(f"Unable to determine path for module: {module}")


def _assert_from_site_packages(module) -> None:
    module_path = _module_path(module)
    assert "site-packages" in module_path.parts or ".venv" in module_path.parts


def test_stub_modules_absent_from_repo() -> None:
    for name in ["azure", "fastapi", "httpx", "pydantic_settings.py", "uvicorn.py"]:
        assert not (PROJECT_ROOT / name).exists()


@pytest.mark.parametrize(
    "module_name",
    ["fastapi", "httpx", "pydantic_settings", "uvicorn"],
)
def test_core_dependency_imports_resolve_to_installed_packages(module_name: str) -> None:
    module = importlib.import_module(module_name)
    _assert_from_site_packages(module)


def test_azure_dependencies_resolve_to_installed_packages() -> None:
    for azure_module in ["azure.identity", "azure.mgmt.logic", "azure.mgmt.web"]:
        module = importlib.import_module(azure_module)
        _assert_from_site_packages(module)
