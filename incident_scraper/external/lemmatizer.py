import logging
import re

import nltk
from textblob import Word

from incident_scraper.utils.constants import INCIDENT_TYPE_INFO
from incident_scraper.utils.functions import custom_title_case


nltk.download("wordnet")


class Lemmatizer:
    @staticmethod
    def process(incident: str) -> str:
        incident = (
            incident.replace("Information / |/ Information ", "")
            .replace("\\", "/")
            .replace(" (", " / ")
            .replace("(", "")
            .replace(")", "")
            .replace("&", "and")
            .replace("Inforation", INCIDENT_TYPE_INFO)
            .replace("Well Being", "Well-Being")
            .replace("Infformation", INCIDENT_TYPE_INFO)
            .replace("Hit & Run", "Hit and Run")
            .replace("Att.", "Attempted")
            .replace("Agg.", "Aggravated")
            .replace("(", "/ ")
            .replace(")", "")
            .replace("\n", " ")
            .replace(" - ", " / ")
            .replace("/", " / ")
            .replace("`", "")
        ).strip()
        incident = custom_title_case(incident)

        incident = (
            incident.replace("Dui", "DUI")
            .replace("Uc", "UC")
            .replace("Uuw", "Unlawful Use of a Weapon")
            .replace("Non Criminal", "Non-Criminal")
            .replace("Non-Criminal / Damage", "Non-Criminal Damage")
        )

        incident = re.sub(r"\s{2,}", " ", incident)

        i_types = []
        updated = False
        for i_type in incident.split(" / "):
            lemma = custom_title_case(
                " ".join(
                    [Word(w.lower()).lemmatize() for w in i_type.split(" ")]
                )
            )
            lemma = (
                lemma.replace("Uc", "UC")
                .replace("UCpd", "UCPD")
                .replace("Duo", "DUI")
                .replace("Dui", "DUI")
                .replace("Mean", "Means")
                .replace("Attempt ", "Attempted ")
            )

            lemma = Lemmatizer.__map_incident_type(lemma)

            if i_type != lemma:
                updated = True
                i_types.append(lemma)
            else:
                i_types.append(i_type)

        if updated:
            lemma_incident = " / ".join(i_types)
            logging.info(
                f"Incident type changed from {incident} to {lemma_incident}."
            )
            return lemma_incident
        else:
            return incident

    @staticmethod
    def __map_incident_type(incident: str) -> str:
        TYPE_MAPPINGS: {str: [str]} = {
            "Aggravated Assault of a Police Officer": [
                "Aggravated Assault of Police Officer"
            ],
            "Aggravated Battery of a Police Officer": [
                "Aggravated Battery of Police Officer",
                "Aggravated Battery to Police Officer",
            ],
            "Assault": ["Simple Assault Battery", "Simple Assault"],
            "Assist Other Agency": [
                "Assist Other Agency Motor Vehicle Theft and Recovery"
            ],
            "Battery": ["Battery-Simple", "Simple Battery"],
            "Battery of a Police Officer": [
                "Battery of Police Officer",
                "Battery to Police Officer",
            ],
            "Criminal Damage to Vehicle": ["Criminal Damage to Motor Vehicle"],
            "Damage to Property": [
                "Criminal Damage to Property",
                "Damage to City Property",
                "Damage to Personal Property",
                "Damage to UC Property",
                "Damage",
                "Damaged Property",
            ],
            "Domestic Assault": [
                "Aggravated Domestic Assault",
                "Domestic Aggravated Assault",
            ],
            "Domestic Battery": [
                "Aggravated Domestic Battery",
                "Domestic Aggravated Battery",
            ],
            "DUI": ["DUI Arrest"],
            "Found Property": ["Found", "Found Key", "Found Wallet"],
            "Harassment by Electronic Means": [
                "Harassing Message",
                "Harassment via Electronic Means",
            ],
            "Harassing Email": ["Harassing Email Message", "Harassing Message"],
            "Harassing Telephone Call": [
                "Harassing Phone Call",
                "Harassment by Telephone",
            ],
            "Hazardous Material Incident": [
                "Haz Mat Event",
                "Haz Mat Incident",
                "Haz Mat",
                "Haz-Mat Incident",
                "Hazardous Material Event",
            ],
            "Hit and Run": [
                "Hit and Run Property Damage",
                "Hit and Run Traffic Crash",
            ],
            "Homicide": ["Murder"],
            "Interference with Police Officer": [
                "Interference with Public Officer"
            ],
            "Liquor Law Violation": ["Illegal Consumption by Minor"],
            "Lost Property": ["Lost", "Lost Phone", "Lost Wallet"],
            "Medical Call": ["Mental Health Call"],
            "Medical Transport": [
                "Mental Health Transport",
                "Mental Transport",
            ],
            "Miscellaneous": [
                "Miscellaneous Incident Report",
                "Miscellaneous Incident",
                "Other",
            ],
            "Obstructing a Police Officer": [
                "Obstruct Police Officer",
                "Obstructing Peace Officer",
                "Obstructing Police",
                "Obstructing a Peace Officer",
            ],
            "Other Crime against Person": ["Other Crime Vs. Person"],
            "Possession of Controlled Substance": [
                "Narcotic Arrest",
                "Narcotic",
                "Possession of Crack Cocaine",
                "Possession of Drug Paraphernalia",
                "Possession of Narcotic with Intent to Deliver",
                "Possession of Narcotic",
            ],
            "Possession of Marijuana": ["Possession of Cannabis"],
            "Property Damage": ["Property Damage Only"],
            "Reckless Discharge of a Firearm": [
                "Aggravated Discharge of a Firearm",
                "Reckless Discharge of Firearm",
                "Reckless Discharge of a Weapon",
            ],
            "Resisting Arrest": ["Resisting Police"],
            "Robbery": [
                "Robbery Arrest",
                "Robbery-Aggravated",
                "Robbery-Strong Arm",
            ],
            "Recovered Vehicle": [
                "Recovered Motor Vehicle",
                "Recovered Vehicle",
                "Recovery of Motor Vehicle",
            ],
            "Recovered Stolen Vehicle": [
                "Recovered Stolen Motor Vehicle",
                "Recovered Motor Vehicle",
                "Stolen Motor Vehicle Recovery",
                "Stolen Vehicle Recovery",
            ],
            "Sexual Abuse": ["Criminal Sexual Abuse"],
            "Sexual Assault": [
                "Aggravated Criminal Sexual Assault",
                "Criminal Sexual Assault",
            ],
            "Strong Arm": ["Strong Armed"],
            "Suspicious Mail": ["Suspicious Letter", "Suspicious Package"],
            "Suspect Narcotic": ["Suspect Narcotic Found"],
            "Traffic Violation Arrest": [
                "Traffic Arrest",
            ],
            "Trespass to Property": [
                "Criminal Trespass to Land",
                "Criminal Trespass to Property",
                "Criminal Trespass to Residence",
                "Criminal Trespass",
                "Trespass to Land",
            ],
            "Trespass to Vehicle": [
                "Criminal Trespass to Motor Vehicle",
                "Criminal Trespass to Vehicle",
                "Trespass to Motor Vehicle",
            ],
            "Unlawful Discharge of a Firearm": [
                "Unlawful Discharge of Firearm",
                "Unlawful Discharge of Weapon",
                "Unlawful Discharge of a Weapon",
            ],
            "Unlawful Possession of a Firearm": [
                "Unlawful Possession of Firearm",
                "Unlawful Possession of Handgun",
                "Unlawful Possession of a Handgun",
            ],
            "Unlawful Possession of a Weapon": [
                "Unlawful Possession of Weapon"
            ],
            "Unlawful Use of a Weapon": [
                "Unlawful Use of Weapon",
                "Unlawful Use of a Weapon Arrest",
            ],
            "Vehicle Theft and Recovery": [
                "Motor Vehicle Theft and Recovery",
                "Motor Vehicle Theft Recovery",
            ],
            "Well-Being Check": ["Well-Being"],
        }

        for true_type, type_list in TYPE_MAPPINGS.items():
            if incident in type_list:
                incident = true_type
                break

        return incident
