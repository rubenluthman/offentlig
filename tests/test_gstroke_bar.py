"""The bar of `Ǥ` in Black keeps clear of the lower curve and the crossbar of the `G` where it begins.

At 5 and 40 units from its left end the bar has at least 30 units of air above and below, in Black and Black Italic.
Before this test the bar began 20 units above the lower curve and then ran into it, leaving a hairline gap.
"""
import pytest
from fontTools.ttLib import TTFont

from conftest import static_path
from test_bar_thickness import polygons, runs

MIN_AIR = 30


@pytest.mark.parametrize("italic", [False, True], ids=["roman", "italic"])
def test_black_gstroke_bar_clears_the_bowl_where_it_begins(italic):
    font = TTFont(static_path("Black", italic))
    cmap = font.getBestCmap()
    g, gstroke = polygons(font, cmap[ord("G")]), polygons(font, cmap[ord("Ǥ")])
    bar_y = 415
    left = runs(gstroke, bar_y, True)[-1][0]
    for dx in (5, 40):
        x = left + dx
        bar = next(r for r in runs(gstroke, x, False) if r[0] <= bar_y <= r[1])
        ink = runs(g, x, False)
        below = max((r[1] for r in ink if r[1] <= bar[0] + 1), default=-1000)
        above = min((r[0] for r in ink if r[0] >= bar[1] - 1), default=10000)
        assert bar[0] - below >= MIN_AIR, f"only {bar[0] - below:.0f} units under the bar at {dx} from its left end"
        assert above - bar[1] >= MIN_AIR, f"only {above - bar[1]:.0f} units over the bar at {dx} from its left end"
