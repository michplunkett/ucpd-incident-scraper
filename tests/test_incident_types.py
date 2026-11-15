from collections import Counter

import pytest

from incident_scraper.utils.incident_types import (
    INCIDENT_TYPE_ALIASES,
    map_incident_type,
    merge_split_types,
    normalize_separators,
    unique_type_names,
)

ALL_ALIASES = [a for aliases in INCIDENT_TYPE_ALIASES.values() for a in aliases]


def clean(incident: str) -> str:
    """The pure part of Lemmatizer.process, applied to a whole value."""
    incident = merge_split_types(normalize_separators(incident))
    return " / ".join(map_incident_type(part) for part in incident.split(" / "))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Theft", "Theft"),
        ("Theft / Battery", "Theft / Battery"),
        ("Information / / Domestic Battery", "Information / Domestic Battery"),
        ("Traffic Crash / Hit and Run /", "Traffic Crash / Hit and Run"),
        ("/ Property Damage", "Property Damage"),
        ("Theft  /  Battery", "Theft / Battery"),
        ("Theft/Battery", "Theft / Battery"),
        ("", ""),
    ],
)
def test_normalize_separators(raw, expected):
    assert normalize_separators(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Non-Criminal / Fire", "Non-Criminal Fire"),
        ("Fire / Non-Criminal", "Non-Criminal Fire"),
        ("Non-Criminal / Damage to Vehicle", "Non-Criminal Damage to Vehicle"),
        (
            "Damage to Property / Non-Criminal",
            "Non-Criminal Damage to Property",
        ),
        ("Non-Criminal / Property Damage", "Non-Criminal Property Damage"),
        (
            "Damage to Property / Non-Criminal / Fire",
            "Damage to Property / Non-Criminal Fire",
        ),
        ("Theft / Attempt", "Attempted Theft"),
        ("Motor Vehicle Theft / Attempted", "Attempted Motor Vehicle Theft"),
        ("Battery / Simple", "Battery"),
        ("Battery / Simple / Theft", "Battery / Theft"),
        ("Harassment / Electronic Means", "Harassment by Electronic Means"),
        ("Fire / Accidental", "Accidental Fire"),
        ("Fleeing / Eluding Police", "Fleeing or Attempting to Elude Police"),
        ("Aggravated Fleeing / Eluding Police", "Aggravated Fleeing"),
        # Distinct types and partial-component matches must be left alone.
        ("Non-Criminal / Weapon Turn-In", "Non-Criminal / Weapon Turn-In"),
        ("Non-Criminal / Fire Alarm", "Non-Criminal / Fire Alarm"),
        ("Non-Criminal / Missing Person", "Non-Criminal / Missing Person"),
        ("Theft / Attempted Burglary", "Theft / Attempted Burglary"),
        (
            "Domestic Battery / Simple Assault",
            "Domestic Battery / Simple Assault",
        ),
    ],
)
def test_merge_split_types(raw, expected):
    assert merge_split_types(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Asist Other Agency", "Assist Other Agency"),
        ("Hir and Run", "Hit and Run"),
        (
            "Fleeing or Attempting to Allude Police",
            "Fleeing or Attempting to Elude Police",
        ),
        (
            "Possession of a Controlled Substance",
            "Possession of Controlled Substance",
        ),
        ("Traffic Accident", "Traffic Crash"),
        ("Motor Vehicle Accident", "Traffic Crash"),
        ("Traffic Crash Hit and Run", "Traffic Crash / Hit and Run"),
        ("Information Harassment", "Information / Harassment"),
        ("Non-Criminal Property Damage", "Non-Criminal Damage to Property"),
        ("Non-Criminal Incident", "Non-Criminal"),
        ("Theft of Motor Vehicle", "Motor Vehicle Theft"),
        ("Aggravated Vehicular Carjacking", "Aggravated Vehicular Hijacking"),
        (
            "Notice of Order of Protection",
            "Notification of Order of Protection",
        ),
        ("Telephone Harassment", "Harassing Telephone Call"),
        ("Suspect Narcotic", "Found Suspect Narcotic"),
        ("Suspect Narcotic Found", "Found Suspect Narcotic"),
        ("Found Suspect Narcotic", "Found Suspect Narcotic"),
        # Behavior that predates these fixes.
        ("Murder", "Homicide"),
        ("Recovered Motor Vehicle", "Recovered Vehicle"),
        ("Harassing Message", "Harassment by Electronic Means"),
        # Canonical and unknown names pass through untouched.
        ("Traffic Crash", "Traffic Crash"),
        ("Theft", "Theft"),
        ("Something New", "Something New"),
    ],
)
def test_map_incident_type(raw, expected):
    assert map_incident_type(raw) == expected


@pytest.mark.parametrize(
    "aliases",
    [
        pytest.param(
            [a for a, n in Counter(ALL_ALIASES).items() if n > 1],
            id="alias listed under two canonicals",
        ),
        pytest.param(
            [a for a in ALL_ALIASES if a in INCIDENT_TYPE_ALIASES],
            id="alias that is also a canonical name",
        ),
    ],
)
def test_alias_table_has_no_conflicts(aliases):
    assert aliases == []


@pytest.mark.parametrize(
    "raw",
    [
        "Traffic Accident / Property Damage",
        "Traffic Crash Property Damage / Hit and Run",
        "Non-Criminal / Fire",
        "Information / Telephone Harassment",
        "Aggravated Fleeing / Attempted to Elude Police",
        "Traffic Crash / Hit and Run /",
        "Battery / Simple / Theft / Damage to Property",
    ],
)
def test_clean_is_idempotent(raw):
    once = clean(raw)
    assert clean(once) == once


@pytest.mark.parametrize(
    ("incidents", "expected"),
    [
        (["Theft", "Battery"], ["battery", "theft"]),
        (["Theft / Battery", "Theft"], ["battery", "theft"]),
        (["Hit and Run /", "Theft"], ["hit and run", "theft"]),
        (["Theft", ""], ["theft"]),
        (["Theft", "  "], ["theft"]),
        ([], []),
        # No blank entry present: this used to raise KeyError.
        (["Information"], ["information"]),
    ],
)
def test_unique_type_names(incidents, expected):
    assert unique_type_names(incidents) == expected
