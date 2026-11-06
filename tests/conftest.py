"""Shared fixtures. Tests run against the built fonts in fonts/OffentligSans (run `make build` first)."""
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "fonts" / "OffentligSans"
WEIGHTS = ["Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black"]


def static_path(weight: str, italic: bool, kind: str = "ttf") -> Path:
    style = "Italic" if italic and weight == "Regular" else weight + ("Italic" if italic else "")
    return BUILD / kind / f"OffentligSans-{style}.{kind}"


def pytest_configure(config):
    if not (BUILD / "ttf").is_dir():
        raise pytest.UsageError("fonts/OffentligSans is missing: run `make build` before `make test`.")


STATICS = [(w, i) for i in (False, True) for w in WEIGHTS]
STATIC_IDS = [f"{w}{'-italic' if i else ''}" for w, i in STATICS]


@pytest.fixture(params=STATICS, ids=STATIC_IDS)
def static_ttf(request):
    weight, italic = request.param
    return TTFont(static_path(weight, italic))


@pytest.fixture(params=[False, True], ids=["roman", "italic"])
def variable_path(request):
    name = "OffentligSans-Italic[wght].ttf" if request.param else "OffentligSans[wght].ttf"
    return BUILD / "variable" / name


@pytest.fixture
def variable_ttf(variable_path):
    return TTFont(variable_path)
