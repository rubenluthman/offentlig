"""Source-level checks on the kerning of the masters."""

import plistlib

import pytest

from conftest import ROOT

UFOS = sorted((ROOT / "sources").glob("OffentligSans*.ufo"))


def load(ufo, name):
    with open(ufo / name, "rb") as f:
        return plistlib.load(f)


def test_the_masters_are_found():
    assert len(UFOS) == 6


@pytest.mark.parametrize("ufo", UFOS, ids=lambda p: p.name)
def test_kerning_keys_name_groups_of_the_same_master(ufo):
    """A `public.kern1.*` first key or `public.kern2.*` second key without a group never reaches the font."""
    groups = load(ufo, "groups.plist")
    missing = set()
    for first, seconds in load(ufo, "kerning.plist").items():
        if first.startswith("public.kern1.") and first not in groups:
            missing.add(first)
        for second in seconds:
            if second.startswith("public.kern2.") and second not in groups:
                missing.add(second)
    assert not missing, f"kerning names groups that do not exist in {ufo.name}: {sorted(missing)}"
