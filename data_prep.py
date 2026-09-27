"""Loading and cleaning for the Lebanon public-spaces dataset.

Same cleaning steps as the Plotly assignment notebook, kept in one module so the
app file stays a plain top-to-bottom script.
"""

from __future__ import annotations

import pandas as pd

CSV_PATH = "data/public_spaces_lebanon_2023.csv"

PARK_COL = "Existence of public parks - exists "  # note: trailing space in the source file

# refArea mixes two administrative levels: 7 governorates appear directly (those
# towns have no district recorded) alongside 18 districts.
DISTRICT_TO_GOV = {
    "Aley": "Mount Lebanon", "Baabda": "Mount Lebanon", "Byblos": "Mount Lebanon",
    "Keserwan": "Mount Lebanon", "Matn": "Mount Lebanon",
    "Batroun": "North", "Bsharri": "North", "Miniyeh–Danniyeh": "North",
    "Tripoli": "North", "Zgharta": "North",
    "Bint Jbeil": "Nabatieh", "Hasbaya": "Nabatieh", "Marjeyoun": "Nabatieh",
    "Hermel": "Baalbek-Hermel",
    "Sidon": "South", "Tyre": "South",
    "Western Beqaa": "Beqaa", "Zahlé": "Beqaa",
}
GOVERNORATES = {"Akkar", "Mount Lebanon", "Baalbek-Hermel", "Beqaa",
                "Nabatieh", "North", "South", "Beirut"}

NO_DISTRICT = "District not specified"
NOT_REPORTED = "Not reported"

COND_COLORS = {
    "Good": "#2a9d8f",
    "Acceptable": "#e9c46a",
    "Bad": "#e76f51",
    "No park / not rated": "#d9d9d9",
    NOT_REPORTED: "#bdbdbd",
}
LIGHT_ORDER = ["Good", "Acceptable", "Bad", NOT_REPORTED]


def _fix_mojibake(s: str) -> str:
    """The published CSV is double-encoded ('ZahlÃ©' instead of 'Zahlé'). Repair it."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def _collapse(row: pd.Series, prefix: str, options: list[tuple[str, str]]) -> str | None:
    """Turn a group of one-hot columns into one label, or None when nothing is flagged."""
    for label, col in options:
        if row[prefix + col] == 1:
            return label
    return None


def load_data(csv_path: str = CSV_PATH) -> pd.DataFrame:
    """Read the published CSV and return one tidy row per town."""
    raw = pd.read_csv(csv_path)

    # The DBpedia refArea URI is the only geography in the file.
    raw["Area"] = (
        raw["refArea"]
        .map(_fix_mojibake)
        .str.rsplit("/", n=1).str[-1]
        .str.replace("_District", "", regex=False)
        .str.replace("_Governorate", "", regex=False)
        .str.replace(",_Lebanon", "", regex=False)
        .str.replace("_", " ", regex=False)
    )
    raw["Governorate"] = [a if a in GOVERNORATES else DISTRICT_TO_GOV[a] for a in raw["Area"]]
    raw["District"] = [NO_DISTRICT if a in GOVERNORATES else a for a in raw["Area"]]

    raw["HasPark"] = raw[PARK_COL].astype(int)
    raw["ParkStatus"] = raw["HasPark"].map({1: "Has a park", 0: "No park"})
    raw["ParkCondition"] = raw.apply(
        _collapse, axis=1, prefix="State of public parks - ",
        options=[("Good", "good"), ("Acceptable", "acceptable "), ("Bad", "bad ")],
    )
    raw["LightCondition"] = raw.apply(
        _collapse, axis=1, prefix="State of the lighting network - ",
        options=[("Good", "good"), ("Acceptable", "acceptable"), ("Bad", "bad")],
    )
    # Missing ratings become their own category rather than being dropped.
    raw["ParkQuality"] = raw["ParkCondition"].fillna("No park / not rated")
    raw["LightQuality"] = raw["LightCondition"].fillna(NOT_REPORTED)

    return raw[["Town", "Governorate", "District", "Area", "HasPark", "ParkStatus",
                "ParkCondition", "ParkQuality", "LightCondition", "LightQuality"]].copy()


def coverage_by(df: pd.DataFrame, level: str) -> pd.DataFrame:
    """Share of towns with a public park, aggregated to `level` (Governorate or District)."""
    out = (
        df.groupby(level)
        .agg(Towns=("Town", "size"), WithPark=("HasPark", "sum"))
        .assign(Coverage=lambda d: d.WithPark / d.Towns * 100)
        .sort_values("Coverage")
        .reset_index()
    )
    return out


def coverage_by_lighting(df: pd.DataFrame) -> pd.DataFrame:
    """Park coverage split by how the town rated its street-lighting network."""
    out = (
        df.groupby("LightQuality")
        .agg(Towns=("Town", "size"), WithPark=("HasPark", "sum"))
        .assign(Coverage=lambda d: d.WithPark / d.Towns * 100)
        .reindex(LIGHT_ORDER)
        .dropna(subset=["Towns"])
        .reset_index()
    )
    out["Towns"] = out["Towns"].astype(int)
    out["WithPark"] = out["WithPark"].astype(int)
    return out
