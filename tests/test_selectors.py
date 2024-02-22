import pytest

from nbmanips import Notebook
from nbmanips.selector import Selector


@pytest.mark.parametrize(
    "cell_num, expected",
    [
        (0, False),
        (1, False),
        (2, True),
        (3, True),
        (4, True),
        (5, False),
        (6, True),
        (7, True),
        (8, False),
    ],
)
def test_has_output(nb3: Notebook, cell_num, expected):
    from nbmanips.cell import Cell
    from nbmanips.selector.default_selector import has_output

    cell = Cell(nb3.cells[cell_num], cell_num)
    assert has_output(cell) == expected


@pytest.mark.parametrize(
    "selector,args,expected",
    [
        ("has_output", (), 1),
        ("contains", ("Hello",), 1),
        ("contains", ("hello", False), 1),  # case=False
        ("contains", ("hello", True), None),  # case=True
    ],
)
def test_selector_args(nb1, selector, args, expected):
    assert nb1.select(selector, *args).first() == expected


@pytest.mark.parametrize(
    "selector,args,expected",
    [
        # (['has_output', 'contains'], (), 3), # TODO: add another error test for this
        (["has_output", "contains"], ({"value": False}, {"text": "5"}), 2),
        (["has_output", "contains"], ([{"value": False}, {"text": "5"}]), 2),
        (["has_output", "contains"], ([{"value": True}, {"text": "5"}]), None),
        (["has_output", "contains"], ([{"value": True}, {"text": "a"}]), 3),
        (["has_output", "contains"], ([{}, {"text": "a"}]), 3),
        (["has_output", "contains"], ({}, {"text": "5"}), None),
        (["has_output", "contains"], ([True], ["a"]), 3),
        (["has_output", "contains"], ({"value": True}, ["a"]), 3),
        (["has_output", "contains"], ({"value": False}, ["5"]), 2),
        (["has_output", "contains"], ([True], (["hello"], {"case": True})), None),
        (["has_output", "contains"], ([True], (("hello",), {"case": True})), None),
        (["has_output", "contains"], ([True], (["hello"], {"case": False})), 1),
        (["has_output", "contains"], ([True], (("hello",), {"case": False})), 1),
    ],
)
def test_list_selector_args(nb1, selector, args, expected):
    assert nb1.select(selector, *args).first() == expected


def test_list_or_selector(nb1):
    selector = Selector(["contains", "contains"], ("o",), {"text": "="}, type="or")
    assert nb1.select(selector).list() == [1, 2]


@pytest.mark.parametrize("slice_", [(0, 3), (1, 3), (1, 1), (0,), (1, 3, 2)])
def test_slice_selector(nb1, slice_: list):
    assert nb1.select(slice(*slice_)).list() == list(range(*slice_))


def test_negative_slice_selector(nb1):
    assert nb1[:-1].list() == [i for i in range(len(nb1))][:-1]
    assert nb1[:-2].list() == [i for i in range(len(nb1))][:-2]
    assert nb1[:-3].list() == [i for i in range(len(nb1))][:-3]
    assert nb1[-3:-1].list() == [i for i in range(len(nb1))][-3:-1]
    assert nb1[-3:-2].list() == [i for i in range(len(nb1))][-3:-2]
    assert set(nb1[3:1:-1].list()) == set([i for i in range(len(nb1))][3:1:-1])
    assert set(nb1[-1:-3:-1].list()) == set([i for i in range(len(nb1))][-1:-3:-1])


@pytest.mark.parametrize("value,expected", [(0, 0), (3, 3), (5, None), (-1, 3)])
def test_int_selector(nb1, value, expected):
    assert nb1.select(value).first() == expected


def test_none_selector(nb1):
    assert nb1.select(None).list() == [i for i in range(len(nb1))]


def test_selector_selector(nb1):
    selector = Selector("contains", "hello", case=False)
    assert nb1.select(selector).first() == 1


@pytest.mark.parametrize("output_type,expected", [("text/plain", [1, 3])])
def test_has_output_type1(nb1, output_type, expected):
    assert nb1.select("has_output_type", output_type).list() == expected


def test_is_empty(nb3):
    assert nb3.select("is_empty").list() == [5, 8]


def test_has_byte_size(nb3):
    assert nb3.select("has_byte_size", min_size=13000).count() == 2
    assert nb3.select("has_byte_size", min_size=13600, ignore_source=True).count() == 1
    assert nb3.select("has_byte_size", min_size=13000, max_size=13700).count() == 1
    assert (
        nb3.select(
            "has_byte_size", min_size=1, output_types="image/png", ignore_source=True
        ).count()
        == 2
    )
    sel = nb3.select(
        "has_byte_size",
        min_size=13455,
        max_size=13456,
        output_types="image/png",
        ignore_source=True,
    )
    assert sel.count() == 2
    assert (
        nb3.select(
            "has_byte_size", min_size=1, output_types="image/jpeg", ignore_source=True
        ).count()
        == 0
    )


def test_and_operator(nb1):
    selector = Selector("contains", "a") & Selector("contains", "=")
    assert nb1.select(selector).list() == [2]


def test_or_operator(nb1):
    selector = Selector("contains", "o") | Selector("contains", "=")
    assert nb1.select(selector).list() == [1, 2]


def test_invert_operator(nb1):
    selector = ~Selector("contains", "o")
    assert nb1.select(selector).list() == [0, 2, 3]


# @pytest.mark.parametrize("output_type,expected",
#                          [('text/plain', [1, 3])])
# def test_has_output_type3(nb3, output_type, expected):
#     assert nb1.find_all('has_output_type', output_type) == expected


def test_has_html_tag(nb6):
    assert nb6.select("has_html_tag", "h1").list() == [0, 8, 12]
    assert nb6.select("has_html_tag", "h2").list() == [2, 4, 12]
    assert nb6.select("has_html_tag", "img").count() == 0


def test_has_tag(nb6_0):
    assert nb6_0.select("has_tag", "toc").count() == 0

    nb6_0[5].add_tag("toc")
    nb6_0[8].add_tag("Toc")

    assert nb6_0.select("has_tag", "Toc").list() == [5, 8]
    assert nb6_0.select("has_tag", "toc", case=True).list() == [5]
    assert nb6_0.select("has_tag", "Toc", case=True).list() == [8]
