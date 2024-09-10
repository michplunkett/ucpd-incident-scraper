import re


def test_replace_calls():
    goal_str = "stuff / thing"
    assert "stuff\n/ thing".replace("\n", " ") == goal_str
    assert r"stuff \ thing".replace("\\", "/") == goal_str


def test_regex_calls():
    assert re.sub(r"\s{2,}", " ", "thing       stuff") == "thing stuff"
    assert re.sub(r"\s{2,}", " ", "thing      / stuff") == "thing / stuff"
