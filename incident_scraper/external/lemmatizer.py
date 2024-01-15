import logging
import re

from textblob import Word

from incident_scraper.utils.constants import INCIDENT_TYPE_INFO


class Lemmatizer:
    @staticmethod
    def process(incident: str) -> str:
        incident = (
            (
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
            )
            .strip()
            .title()
        )

        incident = (
            incident.replace("Dui", "DUI")
            .replace("Uc", "UC")
            .replace("Uuw", "Unlawful Use of a Weapon")
            .replace("/", " / ")
        )

        incident = re.sub(r"\s{2,}", " ", incident)

        i_types = []
        updated = False
        for i_type in incident.split(" / "):
            lemma = " ".join(
                [Word(w.lower()).lemmatize() for w in i_type.split(" ")]
            ).title()
            lemma = (
                lemma.replace("Uc", "UC")
                .replace("UCpd", "UCPD")
                .replace("Duo", "DUI")
                .replace("Dui", "DUI")
                .replace("Mean", "Means")
                .replace("Attempt ", "Attempted ")
            )

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
