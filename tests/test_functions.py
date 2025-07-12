import pytest
from Functions import expand_abbreviations, syllabify_georgian, preprocess_and_syllabify

def test_expand_abbreviations():
    text = "დ.ა.შ."
    expanded = expand_abbreviations(text)
    assert isinstance(expanded, str)
    # Add more specific checks if you know expected output

def test_syllabify_georgian():
    word = "საქართველო"
    sylls = syllabify_georgian(word)
    assert isinstance(sylls, list)
    assert all(isinstance(s, str) for s in sylls)
    assert len(sylls) > 0

def test_preprocess_and_syllabify():
    text = "გამარჯობა საქართველო"
    sylls = preprocess_and_syllabify(text)
    assert isinstance(sylls, list)
    assert all(isinstance(s, str) for s in sylls)
    assert "<s>" in sylls 