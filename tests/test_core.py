from kasa.assistant import Term, check_terms, localize_terms, protected_in
from kasa.bench_mt import bootstrap_chrf, chrf
from kasa.data import COLUMNS

GLOSS = [Term("NHIS", True), Term("Ghana Card", True), Term("health insurance", False, {"twi": "localterm"})]


def test_protected_terms_found_and_checked():
    assert [t.en for t in protected_in("Show your Ghana Card at the NHIS office.", GLOSS)] == ["NHIS", "Ghana Card"]
    r = check_terms("Show your Ghana Card at the NHIS office.", "xx Ghana Card yy NHIS zz.", GLOSS)
    assert r == {"protected": ["NHIS", "Ghana Card"], "kept": ["NHIS", "Ghana Card"]}
    r = check_terms("Bring your Ghana Card.", "xx yy zz.", GLOSS)
    assert r["kept"] == []


def test_local_terms_become_english_before_translation():
    # a placeholder stands in for a local term; real ones come from a speaker
    assert localize_terms("where do I pay localterm?", "twi", GLOSS) == "where do I pay health insurance?"
    assert localize_terms("no change here", "ewe", GLOSS) == "no change here"


def test_chrf_and_bootstrap():
    h = ["the cat sat on the mat", "hello world"] * 20
    r = ["a cat sat on a mat", "hello there world"] * 20
    lo, hi = bootstrap_chrf(h, r, n=200)
    assert lo <= chrf(h, r) <= hi


def test_columns():
    assert COLUMNS[:5] == ["id", "set", "lang", "en", "local"]
