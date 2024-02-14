import re
from typing import Tuple


class AddressParser:
    """
    A singleton class that contains all address parsing functions.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.numerical_streets = [self._make_ordinal(s) for s in range(37, 95)]
        self.street_corrections = [
            self._create_street_tuple("Blackstone"),
            self._create_street_tuple("Cottage Grove"),
            self._create_street_tuple("Cornell"),
            self._create_street_tuple("Dorchester"),
            self._create_street_tuple("Drexel"),
            self._create_street_tuple("East End"),
            self._create_street_tuple("East View Park"),
            self._create_street_tuple("Ellis"),
            self._create_street_tuple("Everett"),
            self._create_street_tuple("Greenwood"),
            self._create_street_tuple("Harper"),
            self._create_street_tuple("Hyde Park", blvd=True),
            self._create_street_tuple("Ingleside"),
            self._create_street_tuple("Kenwood"),
            self._create_street_tuple("Kimbark"),
            self._create_street_tuple("Lake Park"),
            ("Lake Shore", "S. Lake Shore", "S. Lake Shore Dr."),
            ("Madison Park", "E. Madison Park", "E. Madison Park"),
            self._create_street_tuple("Maryland"),
            self._create_street_tuple("Oakenwald"),
            self._create_street_tuple("Oakwood", blvd=True),
            ("Ridgewood", "S. Ridgewood", "S. Ridgewood Ct."),
            ("State", "S. State", "S. State St."),
            self._create_street_tuple("Stony Island"),
            self._create_street_tuple("University"),
            self._create_street_tuple("Woodlawn"),
        ]
        self.street_corrections_final = [
            s for _, _, s in self.street_corrections
        ]
        self.street_corrections_final.extend(
            ["S. Shore Dr.", "Midway Plaisance"]
        )

    @staticmethod
    def _create_street_tuple(
        street: str, blvd: bool = False
    ) -> Tuple[str, str, str]:
        street_type = "Ave." if not blvd else "Blvd."

        return street, f"S. {street}", f"S. {street} {street_type}"

    # Source: https://stackoverflow.com/a/50992575
    @staticmethod
    def _make_ordinal(n: int) -> str:
        """
        Convert an integer into its ordinal representation::

            make_ordinal(0)   => '0th'
            make_ordinal(3)   => '3rd'
            make_ordinal(122) => '122nd'
            make_ordinal(213) => '213th'
        """
        if 11 <= (n % 100) <= 13:
            suffix = "th"
        else:
            suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
        return str(n) + suffix

    def _correct_ordinals(self, address: str) -> str:
        for s in self.numerical_streets:
            dir_s = f"E. {s}"
            if s in address and dir_s not in address:
                address = address.replace(s, dir_s)

            full_s = f"{dir_s} St."
            if (
                dir_s in address
                and full_s not in address
                and f"{s} Pl" not in address
            ):
                address = address.replace(dir_s, full_s)

        return address

    def _correct_non_ordinals(self, address: str) -> str:
        for sc in self.street_corrections:
            if "E. S. Harper Ave. Ct." in address:
                address = address.replace(
                    "E. S. Harper Ave. Ct.", "E. Harper Ct."
                )
                break

            if "S. Harper Ave. Ct." in address:
                address = address.replace(
                    "S. Harper Ave. Ct.", "S. Harper Ave."
                )
                break

            if "E. S. Hyde Park Blvd." in address:
                address = address.replace(
                    "E. S. Hyde Park Blvd.", "E. Hyde Park Blvd."
                )
                break

            name, dir_name, full_name = sc

            if name in address and dir_name not in address:
                address = address.replace(name, dir_name)

            if dir_name in address and full_name not in address:
                address = address.replace(dir_name, full_name)

        non_ordinal_streets = [
            s for s in self.street_corrections_final if s in address
        ]
        if (
            len(non_ordinal_streets) == 3
            and "S. Hyde Park Blvd." in non_ordinal_streets
        ):
            address = address.replace(
                "S. Hyde Park Blvd.", "E. Hyde Park Blvd."
            )

        return address

    @staticmethod
    def _correct_replacements(address: str) -> str:
        address = re.sub(r"\s{2,}", " ", address)
        address = re.sub(r" Drive$", " Dr.", address)
        address = re.sub(r" Court$", " Ct.", address)
        address = re.sub(r"^Shore Dr.", "S. Shore Dr.", address)
        address = re.sub("St. St,?", "St.", address)
        address = re.sub("Dr. Dr,?", "Dr.", address)
        address = re.sub(r"E,?\.? E\.", "E.", address)
        address = re.sub(r"S,?\.? S\.", "S.", address)
        address = re.sub(
            r"\(?S. Woodlawn Ave. Charter School\)?$",
            "(S. Woodlawn Ave. Charter School)",
            address,
        )

        address = (
            address.replace("&", "and")
            .replace("..", ".")
            .replace("South S.", "S.")
            .replace("East E.", "E.")
            .replace("\n", " ")
            .replace("Ave. Ave", "Ave.")
            .replace("Blvd. Blvd", "Blvd.")
            .replace("St. Street", "St.")
            .replace(" Drive ", " Dr. ")
            .replace(" Dr ", " Dr. ")
            .replace(" s. ", " S. ")
            .replace(" e. ", " E. ")
            .replace("S. S.", "S.")
            .replace("E. E.", "E.")
            .replace(" st. ", " St. ")
            .replace("St..", "St.")
            .replace("St. St.", "St.")
            .replace(" Court ", " Ct. ")
            .replace(" Pl ", " Pl. ")
            .replace(" pl. ", " Pl. ")
            .replace("Midway Pl.", "Midway Plaisance")
            .replace("South Shore", "S. Shore")
            .replace("Woodland", "Woodlawn")
            .replace("Between", "between")
            .replace(" and Shore Dr.", " and S. Shore Dr.")
        )

        return address

    def process(self, address: str) -> str:
        address = self._correct_replacements(address)
        address = self._correct_ordinals(address)
        address = self._correct_non_ordinals(address)

        return address
