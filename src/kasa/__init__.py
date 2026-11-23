"""A chat assistant for Twi (Akan), Ga, Ewe and Hausa, with measured translation and terminology."""

__version__ = "0.1.0"

LANGS = {
    "twi": {"name": "Twi (Akan)", "nllb": "twi_Latn", "flores": "twi_Latn"},
    "ewe": {"name": "Ewe", "nllb": "ewe_Latn", "flores": "ewe_Latn"},
    "gaa": {"name": "Ga", "nllb": None, "flores": None},
    "hau": {"name": "Hausa", "nllb": "hau_Latn", "flores": "hau_Latn"},
}
