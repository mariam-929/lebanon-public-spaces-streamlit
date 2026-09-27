# Public spaces in Lebanon — interactive drill-down

An interactive Streamlit page about public parks in Lebanon's 1,137 towns, built for the
Visualization & Communication course (AUB, Fall 2026). It extends my Plotly assignment,
using the same dataset and the same cleaning steps.

**Live app:** _add the Streamlit Community Cloud link here after deploying_

## What the page shows

Two linked charts:

1. **Where the parks are** — the share of towns with a public park, by governorate, or by
   district once a governorate is selected. A dashed line marks the national average (32.8%).
2. **Parks vs street lighting** — park coverage split by how each town rates its street-lighting
   network, including towns that never answered.

Two insights it is built to surface:

- **Mount Lebanon underperforms.** The largest, most urban governorate is second from last, at
  25.9% of towns, against a national 32.8%.
- **Missing answers are the signal.** Towns that never rated their lighting network have a park
  rate of 16.2%, less than half the rate of towns that answered.

## The two linked controls

- **Governorate** (single-select dropdown) sets the scope.
- **Districts** (multiselect) is populated *from the chosen governorate*, so the reader drills
  down instead of filtering two things independently. Selecting a governorate also switches the
  first chart from governorate level to district level. Governorates with no district recorded
  in the source data disable the control with an explanation.

The reasoning behind each control is written on the page itself, under "Why these two controls".

## Data

`data/public_spaces_lebanon_2023.csv` — *Public spaces – Lebanon 2023*, Impact Open Data /
Government of Lebanon, published through AUB's PKGCube.

Three quirks handled in `data_prep.py`:

- the published CSV is double-encoded (`ZahlÃ©` → `Zahlé`);
- `refArea` mixes governorates and districts, so a district → governorate map is applied and
  towns with no district are labelled "District not specified" rather than guessed at;
- several column names carry trailing spaces (`"Existence of public parks - exists "`).

Missing ratings are always shown as their own category, never dropped.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Files

| File | Purpose |
|---|---|
| `streamlit_app.py` | the page: layout, controls, charts, written justifications |
| `data_prep.py` | loading, cleaning and the two aggregations |
| `data/public_spaces_lebanon_2023.csv` | the dataset |
| `requirements.txt` | dependencies for Streamlit Community Cloud |
