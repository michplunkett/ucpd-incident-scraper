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
            "Aggravated Battery of a Police Officer": [
                "Aggravated Battery of Police Officer",
                "Aggravated Battery to Police Officer",
            ],
            "Assault": ["Simple Assault Battery", "Simple Assault"],
            "Battery": ["Battery-Simple", "Simple Battery"],
            "Battery of a Police Officer": [
                "Battery of Police Officer",
                "Battery to Police Officer",
            ],
            "Criminal Damage to Vehicle": ["Criminal Damage to Motor Vehicle"],
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
            "Homicide": ["Murder"],
            "Interference with Police Officer": [
                "Interference with Public Officer"
            ],
            "Lost Property": ["Lost", "Lost Phone", "Lost Wallet"],
            "Motor Vehicle Theft and Recovery": [
                "Motor Vehicle Theft Recovery"
            ],
            "Other Crime against Person": ["Other Crime Vs. Person"],
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
            "Recovered Stolen Motor Vehicle": [
                "Stolen Motor Vehicle Recovery",
                "Stolen Vehicle Recovery",
            ],
            "Strong Arm": ["Strong Armed"],
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
            "Well-Being Check": ["Well-Being"],
        }

        for true_type, type_list in TYPE_MAPPINGS.items():
            if incident in type_list:
                incident = true_type
                break

        return incident
