import re

# Canonical incident type -> variants that should be rewritten to it. Aliases
# are matched against a single, already title-cased and lemmatized component
# (the text between " / " separators). A canonical may itself contain " / " to
# restore a separator the source dropped.
INCIDENT_TYPE_ALIASES: dict[str, tuple[str, ...]] = {
    "Aggravated Assault of a Police Officer": (
        "Aggravated Assault of Police Officer",
    ),
    "Aggravated Battery of a Police Officer": (
        "Aggravated Battery of Police Officer",
        "Aggravated Battery to Police Officer",
    ),
    "Aggravated Fleeing": (
        "Aggravated Fleeing Police",
        "Aggravated Fleeing and Eluding",
    ),
    "Aggravated Vehicular Hijacking": ("Aggravated Vehicular Carjacking",),
    "Assault": ("Simple Assault Battery", "Simple Assault"),
    "Assist Other Agency": (
        "Asist Other Agency",
        "Assist Other Agency Motor Vehicle Theft and Recovery",
    ),
    "Attempted Motor Vehicle Theft": ("Attempted Theft of Motor Vehicle",),
    "Battery": ("Battery-Simple", "Simple Battery"),
    "Battery of a Police Officer": (
        "Battery of Police Officer",
        "Battery to Police Officer",
    ),
    "Confidence Game": ("Con Game",),
    "Criminal Damage to Vehicle": (
        "Criminal Damage to Motor Vehicle",
        "Criminal Defacement to Vehicle",
    ),
    "Damage to Property": (
        "Criminal Damage to Property",
        "Damage to City Property",
        "Damage to Personal Property",
        "Damage to UC Property",
        "Damage",
        "Damaged Property",
    ),
    "Damage to Vehicle": (
        "Damage to UC Owned Vehicle",
        "Damage to UC Vehicle",
        "Vehicle Damage",
    ),
    "Domestic Assault": (
        "Aggravated Domestic Assault",
        "Domestic Aggravated Assault",
    ),
    "Domestic Battery": (
        "Aggravated Domestic Battery",
        "Domestic Aggravated Battery",
    ),
    "Domestic Disturbance": ("Domestic Dispute", "Domestic Issue"),
    "DUI": ("DUI Arrest",),
    "Fleeing or Attempting to Elude Police": (
        "Fleeing or Attempting to Allude Police",
        "Fleeing and Eluding Police",
        "Fleeing Police",
    ),
    "Found Property": ("Found", "Found Key", "Found Wallet"),
    "Harassment by Electronic Means": (
        "Harassing Message",
        "Harassment via Electronic Means",
    ),
    "Harassing Email": ("Harassing Email Message",),
    "Harassing Telephone Call": (
        "Harassing Phone Call",
        "Harassment by Telephone",
        "Telephone Harassment",
    ),
    "Hazardous Material Incident": (
        "Haz Mat Event",
        "Haz Mat Incident",
        "Haz Mat",
        "Haz-Mat Incident",
        "Hazardous Material Event",
    ),
    "Hit and Run": (
        "Hir and Run",
        "Hit and Run Property Damage",
        "Hit and Run Traffic Crash",
    ),
    "Homicide": ("Murder",),
    "Information": ("Information Report", "Campus Information Report"),
    "Information / Damage to Property": (
        "Information Criminal Damage to Property",
    ),
    "Information / Harassment": ("Information Harassment",),
    "Interference with Police Officer": (
        "Interference with Police",
        "Interference with Public Officer",
        "Interfere with Police",
    ),
    "Liquor Law Violation": ("Illegal Consumption by Minor",),
    "Lost Property": ("Lost", "Lost Phone", "Lost Wallet"),
    "Medical Call": ("Mental Health Call",),
    "Medical Transport": ("Mental Health Transport", "Mental Transport"),
    "Minor Personal Injury": ("Minor Injury",),
    "Miscellaneous": (
        "Miscellaneous Incident Report",
        "Miscellaneous Incident",
        "Other",
    ),
    "Motor Vehicle Theft": ("Theft of Motor Vehicle",),
    "Narcotic Delivery": ("Deliver Narcotic", "Delivery of Cannabis"),
    "Non-Criminal": (
        "Non-Criminal Complaint",
        "Non-Criminal Event",
        "Non-Criminal Incident",
        "Non-Criminal Offense",
        "Non-Criminal Other",
        "Non-Criminal Report",
    ),
    "Non-Criminal Damage to Property": (
        "Non-Criminal Damage",
        "Non-Criminal Property Damage",
    ),
    "Notification of Order of Protection": (
        "Notice of Order of Protection",
        "Order of Protection Notification",
    ),
    "Obstructing a Police Officer": (
        "Obstruct Police Officer",
        "Obstructing Peace Officer",
        "Obstructing Police",
        "Obstructing Police Officer",
        "Obstructing a Peace Officer",
    ),
    "Other Crime against Person": ("Other Crime Vs. Person",),
    "Possession of Controlled Substance": (
        "Narcotic Arrest",
        "Narcotic",
        "Narcotic Possession",
        "Possession of a Controlled Substance",
        "Possession of Crack Cocaine",
        "Possession of Drug Paraphernalia",
        "Possession of Narcotic with Intent to Deliver",
        "Possession of Narcotic",
    ),
    "Possession of Marijuana": ("Possession of Cannabis",),
    "Property Damage": ("Property Damage Only",),
    "Reckless Discharge of a Firearm": (
        "Aggravated Discharge of a Firearm",
        "Reckless Discharge of Firearm",
        "Reckless Discharge of a Weapon",
    ),
    "Recovered Stolen Vehicle": (
        "Recovered Stolen Motor Vehicle",
        "Stolen Motor Vehicle Recovery",
        "Stolen Vehicle Recovery",
    ),
    "Recovered Vehicle": (
        "Recovered Motor Vehicle",
        "Recovery of Motor Vehicle",
    ),
    "Resisting Arrest": (
        "Resist Police Officer",
        "Resisting",
        "Resisting Police",
    ),
    "Robbery": ("Robbery Arrest", "Robbery-Aggravated", "Robbery-Strong Arm"),
    "Sexual Abuse": ("Criminal Sexual Abuse",),
    "Sexual Assault": (
        "Aggravated Criminal Sexual Assault",
        "Criminal Sexual Assault",
    ),
    "Sick Person": ("Ill Person",),
    "Strong Arm": ("Strong Armed",),
    "Suspect Narcotic": ("Suspect Narcotic Found",),
    "Suspicious Mail": ("Suspicious Letter", "Suspicious Package"),
    "Telephone Threat": ("Threatening Phone Call", "Threatening Call"),
    "Theft from Motor Vehicle": ("Theft from Vehicle",),
    "Traffic Crash": (
        "Motor Vehicle Accident",
        "Traffic Accident",
        "Traffic Collision",
        "Traffic Crash Report",
        "Vehicle Crash",
    ),
    "Traffic Crash / Arrest": ("Traffic Crash Arrest",),
    "Traffic Crash / Hit and Run": ("Traffic Crash Hit and Run",),
    "Traffic Crash / Property Damage": ("Traffic Crash Property Damage",),
    "Traffic Violation": ("Traffic", "Traffic Offense"),
    "Traffic Violation Arrest": ("Traffic Arrest",),
    "Traffic Violation / Warrant Arrest": (
        "Traffic Violation and Warrant Arrest",
        "Traffic and Warrant Arrest",
    ),
    "Trespass to Property": (
        "Criminal Trespass to Land",
        "Criminal Trespass to Property",
        "Criminal Trespass to Residence",
        "Criminal Trespass",
        "Trespass to Land",
        "Trespass",
    ),
    "Trespass to Vehicle": (
        "Criminal Trespass to Motor Vehicle",
        "Criminal Trespass to Vehicle",
        "Trespass to Motor Vehicle",
    ),
    "Unlawful Discharge of a Firearm": (
        "Unlawful Discharge of Firearm",
        "Unlawful Discharge of Weapon",
        "Unlawful Discharge of a Weapon",
    ),
    "Unlawful Possession of a Firearm": (
        "Unlawful Possession of Firearm",
        "Unlawful Possession of Handgun",
        "Unlawful Possession of a Handgun",
    ),
    "Unlawful Possession of a Weapon": ("Unlawful Possession of Weapon",),
    "Unlawful Use of a Weapon": (
        "Unlawful Use of Weapon",
        "Unlawful Use of a Weapon Arrest",
    ),
    "Vehicle Theft and Recovery": (
        "Motor Vehicle Theft and Recovery",
        "Motor Vehicle Theft Recovery",
        "Theft and Recovery of Motor Vehicle",
    ),
    "Vehicular Hijacking": (
        "Vehicle Hijacking",
        "Vehicular Carjacking",
        "Carjacking",
    ),
    "Warrant Arrest": ("Arrest on Warrant", "UCPD Arrest Warrant"),
    "Well-Being Check": ("Well-Being",),
}

_CANONICAL_BY_ALIAS = {
    alias: canonical
    for canonical, aliases in INCIDENT_TYPE_ALIASES.items()
    for alias in aliases
}

# Source slashes that split one type into pieces, rejoined as one type.
_NON_CRIMINAL_QUALIFIERS = (
    "Damage to Property",
    "Damage to Vehicle",
    "Property Damage",
    "Damage",
    "Property",
    "Fire",
)
_SPLIT_TYPE_FIXES = (
    ("Theft / Attempt", "Attempted Theft"),
    ("Motor Vehicle Theft / Attempted", "Attempted Motor Vehicle Theft"),
    ("Battery / Simple", "Battery"),
    ("Harassment / Electronic Means", "Harassment by Electronic Means"),
    ("Fire / Accidental", "Accidental Fire"),
    ("Fleeing / Eluding Police", "Fleeing or Attempting to Elude Police"),
    ("Aggravated Fleeing / Eluding Police", "Aggravated Fleeing"),
    ("Aggravated Fleeing / Attempted to Elude Police", "Aggravated Fleeing"),
)


def _whole_components(pattern: str) -> re.Pattern[str]:
    """Match `pattern` only when it spans entire " / "-separated components."""
    return re.compile(rf"(?:(?<= / )|^)(?:{pattern})(?= / |$)")


_QUALIFIER_ALTERNATION = "|".join(map(re.escape, _NON_CRIMINAL_QUALIFIERS))
_SPLIT_TYPE_REWRITES = (
    *(
        (_whole_components(re.escape(source)), target)
        for source, target in _SPLIT_TYPE_FIXES
    ),
    *(
        (_whole_components(pattern), r"Non-Criminal \1")
        for pattern in (
            rf"Non-Criminal / ({_QUALIFIER_ALTERNATION})",
            rf"({_QUALIFIER_ALTERNATION}) / Non-Criminal",
        )
    ),
)


def normalize_separators(incident: str) -> str:
    """Collapse doubled or dangling " / " separators ("A / / B", "A /")."""
    return re.sub(r"\s*/[\s/]*", " / ", incident).strip(" /")


def merge_split_types(incident: str) -> str:
    """Rejoin types the source split across slashes ("Non-Criminal / Fire")."""
    for pattern, replacement in _SPLIT_TYPE_REWRITES:
        incident = pattern.sub(replacement, incident)
    return incident


def map_incident_type(incident: str) -> str:
    """Return the canonical name for one component, or it unchanged."""
    return _CANONICAL_BY_ALIAS.get(incident, incident)
