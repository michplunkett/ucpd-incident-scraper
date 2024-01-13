import nltk
from nltk import WordNetLemmatizer


class Lemmatizer:
    nltk.download("wordnet", download_dir="./data")

    def __init__(self):
        self.client = WordNetLemmatizer()

    def process(self, incident: str) -> str:
        i_types = []
        updated = False
        for i_type in incident.split(" / "):
            lemma = " ".join(
                [self.client.lemmatize(w.lower()) for w in i_type.split(" ")]
            ).title()
            lemma = (
                lemma.replace("Uc", "UC")
                .replace("UCpd", "UCPD")
                .replace("Duo", "DUI")
                .replace("Mean", "Means")
            )

            if i_type != lemma:
                updated = True
                i_types.append(lemma)
            else:
                i_types.append(i_type)

        return " / ".join(i_types) if updated else incident
