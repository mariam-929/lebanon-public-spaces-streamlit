"""Public spaces in Lebanon (2023) — an interactive drill-down.

Two linked controls: picking a governorate changes which districts can be chosen,
and both charts follow the resulting selection.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from data_prep import (
    COND_COLORS,
    LIGHT_ORDER,
    NO_DISTRICT,
    NOT_REPORTED,
    coverage_by,
    coverage_by_lighting,
    load_data,
)

st.set_page_config(
    page_title="Public spaces in Lebanon",
    page_icon=":material/park:",
    layout="wide",
)

ALL = "All Lebanon"
TEAL, SLATE = "#2a9d8f", "#264653"


@st.cache_data(ttl=3600)
def get_data() -> pd.DataFrame:
    return load_data()


df = get_data()
national_coverage = df["HasPark"].mean() * 100

# ── Page header ──────────────────────────────────────────────────────────────
st.title("Public spaces in Lebanon")
st.caption(
    "Every one of Lebanon's 1,137 towns, from the 2023 *Public spaces* survey "
    "(Impact Open Data, Government of Lebanon, via AUB's PKGCube). Each town reports "
    "whether it has a public park, what condition that park is in, and how it rates its "
    "street-lighting network."
)

with st.expander("About this data — read this before drawing conclusions"):
    st.markdown(
        """
        - **One row per town, no population figures.** The survey records towns, not people,
          so *coverage* here always means **the share of towns** that have a park, never the
          share of residents served. A governorate of small villages and one of large cities
          count the same way.
        - **The geography comes in two levels.** The published `refArea` field tags some towns
          with a district and others only with a governorate. Towns with no district recorded
          are grouped as *"District not specified"* rather than being assigned a district by guesswork.
        - **Missing ratings are shown, not dropped.** 234 towns (20.6%) never rated their lighting
          network; they appear as *"Not reported"*. 3 towns report a park with no condition rating.
        - **Condition ratings are self-reported** by each town, so "good" is not a measured standard.
        """
    )

# ── The two linked controls ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Drill down")

    gov_options = [ALL] + sorted(df["Governorate"].unique())
    governorate = st.selectbox(
        "Governorate",
        gov_options,
        help="Pick a governorate to change which districts are available below.",
    )

    scope = df if governorate == ALL else df[df["Governorate"] == governorate]

    district_options = sorted(scope["District"].unique())
    has_districts = district_options != [NO_DISTRICT]

    if governorate == ALL:
        # Nothing to drill into yet: the district list only means something inside one
        # governorate, and showing all 19 at once would just be clutter.
        st.multiselect(
            "Districts",
            ["Pick a governorate first"],
            default=["Pick a governorate first"],
            disabled=True,
            help="Choose a governorate above to unlock its districts.",
        )
    elif has_districts:
        districts = st.multiselect(
            "Districts" + ("" if governorate == ALL else f" in {governorate}"),
            district_options,
            default=district_options,
            # The key changes with the governorate so the list resets instead of
            # keeping districts that no longer exist in the new selection.
            key=f"districts::{governorate}",
            help="Options come from the governorate chosen above.",
        )
        if districts:
            scope = scope[scope["District"].isin(districts)]
        else:
            st.warning("No districts selected — showing the whole governorate.")
    else:
        st.multiselect(
            f"Districts in {governorate}",
            [NO_DISTRICT],
            default=[NO_DISTRICT],
            disabled=True,
            help=(
                f"{governorate} has no district recorded in the published data, "
                "so there is nothing to drill into here."
            ),
        )

    st.divider()
    st.caption(
        f"**{len(scope):,}** of {len(df):,} towns in view"
        + ("" if governorate == ALL else f" · {governorate}")
    )

selection_label = ALL if governorate == ALL else governorate
level = "Governorate" if governorate == ALL else "District"

# ── Headline numbers for the current selection ───────────────────────────────
coverage = scope["HasPark"].mean() * 100
delta = coverage - national_coverage

a, b, c, d = st.columns(4)
a.metric("Towns in view", f"{len(scope):,}")
b.metric("Towns with a park", f"{int(scope['HasPark'].sum()):,}")
c.metric(
    "Coverage",
    f"{coverage:.1f}%",
    delta=None if governorate == ALL else f"{delta:+.1f} pts vs national",
    delta_color="normal",
)
rated_good = (scope["ParkCondition"] == "Good").sum()
d.metric(
    "Parks rated good",
    f"{rated_good:,}",
    help="Towns whose park is rated in good condition (self-reported).",
)

st.divider()

# ── Chart 1: coverage by area ────────────────────────────────────────────────
left, right = st.columns([3, 2])

with left:
    st.subheader(
        "Where the parks are"
        if governorate == ALL
        else f"Where the parks are in {governorate}"
    )
    by_area = coverage_by(scope, level)

    if by_area.empty:
        st.info("Nothing to show for this selection.")
    else:
        fig = px.bar(
            by_area,
            x="Coverage",
            y=level,
            orientation="h",
            text=by_area["Coverage"].map("{:.1f}%".format),
            color="Coverage",
            color_continuous_scale=["#8fcac4", "#14425a"],
            custom_data=["WithPark", "Towns"],
            labels={"Coverage": "Towns with a public park (%)"},
        )
        fig.update_traces(
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>%{customdata[0]} of %{customdata[1]} towns"
                          "<br>Coverage: %{x:.1f}%<extra></extra>",
        )
        fig.add_vline(
            x=national_coverage,
            line_dash="dash",
            line_color=SLATE,
            annotation_text=f"National average {national_coverage:.1f}%",
            annotation_position="bottom right",  # bottom stays clear of the longest bar's label
            annotation_font_color=SLATE,
        )
        fig.update_layout(
            template="plotly_white",
            coloraxis_showscale=False,
            xaxis_title="Towns with a public park (%)",
            yaxis_title=None,
            xaxis_range=[0, max(70, by_area["Coverage"].max() * 1.25)],
            margin=dict(l=10, r=30, t=36, b=40),  # room for the national-average label
            height=max(320, 38 * len(by_area) + 90),
        )
        st.plotly_chart(fig, key="coverage_chart")
        st.caption(
            "Dashed line: the national average across all 1,137 towns. "
            "Bars show the share of towns, not of people."
        )

# ── Chart 2: coverage by lighting rating ─────────────────────────────────────
with right:
    st.subheader("Parks vs street lighting")
    by_light = coverage_by_lighting(scope)

    if by_light.empty or len(scope) == 0:
        st.info("Nothing to show for this selection.")
    else:
        fig2 = px.bar(
            by_light,
            x="LightQuality",
            y="Coverage",
            text=by_light["Coverage"].map("{:.1f}%".format),
            color="LightQuality",
            color_discrete_map=COND_COLORS,
            category_orders={"LightQuality": LIGHT_ORDER},
            custom_data=["WithPark", "Towns"],
        )
        fig2.update_traces(
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{x}</b><br>%{customdata[0]} of %{customdata[1]} towns"
                          "<br>Park coverage: %{y:.1f}%<extra></extra>",
        )
        fig2.update_layout(
            template="plotly_white",
            showlegend=False,
            xaxis_title="Town's rating of its street-lighting network",
            yaxis_title="Towns with a public park (%)",
            yaxis_range=[0, max(60, by_light["Coverage"].max() * 1.3)],
            margin=dict(l=10, r=10, t=10, b=40),
            height=max(320, 38 * len(by_area) + 90) if not by_area.empty else 420,
        )
        st.plotly_chart(fig2, key="lighting_chart")
        st.caption(
            "Towns that never answered the lighting question are kept as their own bar "
            "instead of being dropped."
        )

# ── The two insights ─────────────────────────────────────────────────────────
st.divider()
st.subheader("Two things this page is meant to show")

ml = df[df["Governorate"] == "Mount Lebanon"]
ml_cov = ml["HasPark"].mean() * 100
gov_table = coverage_by(df, "Governorate")  # sorted ascending by coverage
ml_rank = int(gov_table.reset_index(drop=True).index[gov_table["Governorate"] == "Mount Lebanon"][0]) + 1
ml_rank_label = {1: "lowest", 2: "2nd lowest", 3: "3rd lowest"}.get(ml_rank, f"{ml_rank}th lowest")
n_govs = gov_table.shape[0]

light_table = coverage_by_lighting(df)
reported = light_table[light_table["LightQuality"] != NOT_REPORTED]
not_reported = light_table[light_table["LightQuality"] == NOT_REPORTED]
reported_cov = reported["WithPark"].sum() / reported["Towns"].sum() * 100
nr_cov = float(not_reported["Coverage"].iloc[0])

i1, i2 = st.columns(2)
with i1.container(border=True):
    st.markdown(f"##### 1. Mount Lebanon underperforms badly")
    st.markdown(
        f"""
        Lebanon's largest and most urban governorate has a park in only
        **{ml_cov:.1f}%** of its {len(ml):,} towns — **{ml_rank_label} of the {n_govs}**
        governorates in this survey, below the national **{national_coverage:.1f}%**
        and far behind Beqaa.
        Set the governorate filter to *Mount Lebanon* and the district list shows the
        spread inside it, so this is not one weak district dragging an average down.
        """
    )
with i2.container(border=True):
    st.markdown("##### 2. The missing answers are the signal")
    st.markdown(
        f"""
        Towns that **never rated their lighting network** have a park rate of
        **{nr_cov:.1f}%**, against **{reported_cov:.1f}%** among towns that answered —
        under half. Whether a town has a park tracks *whether it reports at all*, more
        closely than it tracks whether the lighting it reports is good or bad. That points
        at administrative capacity rather than wealth or terrain.
        """
    )

# ── Design justifications (assignment requirement) ───────────────────────────
st.divider()
st.subheader("Why these two controls")

with st.expander("Control 1 — Governorate (single-select dropdown)"):
    st.markdown(
        """
        **The question it answers:** *"Is the national picture true where I live?"* A single
        national figure (32.8% of towns) hides a range that runs from Akkar at 23.6% to
        Beqaa at 55.2%, so the reader needs to move from the country to one region.

        **Why a dropdown, not the alternatives:** there are seven governorates in this survey,
        and only one can be the scope at a time. `st.pills` or `st.segmented_control` would put
        all seven on screen, but they
        would compete visually with the charts and wrap awkwardly on a laptop. A multiselect
        would let a reader combine, say, Akkar and Beirut into one bar — a comparison with no
        real-world meaning. The dropdown enforces one scope at a time, which is what the
        drill-down needs.

        **Course concept — reducing clutter, and context:** the control collapses eight options
        into one line, and the selected scope is always restated next to the charts, in the
        metrics row and in the national-average line, so a filtered view is never mistaken for
        the whole country.
        """
    )

with st.expander("Control 2 — Districts (multiselect, options driven by control 1)"):
    st.markdown(
        """
        **The question it answers:** *"Inside this region, is coverage even, or is one district
        pulling the average?"* This is the follow-up question, and it only makes sense once a
        governorate is chosen.

        **How it is linked:** the options in this control are generated from the governorate
        chosen above, never from the full list of 18 districts. Choosing *North* offers only
        Batroun, Bsharri, Miniyeh–Danniyeh, Tripoli and Zgharta. The first chart also changes
        level with the selection: governorate bars for all of Lebanon, district bars once a
        governorate is picked. Akkar has no district recorded anywhere in the published data,
        so there the control is disabled with a note rather than showing an empty list.

        **Why a multiselect, not the alternatives:** comparing two or three districts against
        each other is the point, so the control has to allow several at once, which rules out a
        selectbox. Checkboxes would need one widget per district and would not reset when the
        governorate changes.

        **Course concept — focusing attention and honest comparison:** removing districts
        removes bars but keeps the national reference line in place, so a narrowed selection is
        still read against the same yardstick instead of a rescaled one.
        """
    )

# ── Town-level detail ────────────────────────────────────────────────────────
with st.expander(f"See the {len(scope):,} towns behind these charts"):
    st.dataframe(
        scope[["Town", "Governorate", "District", "ParkStatus", "ParkQuality", "LightQuality"]]
        .sort_values(["Governorate", "District", "Town"])
        .rename(columns={
            "ParkStatus": "Public park",
            "ParkQuality": "Park condition",
            "LightQuality": "Lighting network",
        }),
        hide_index=True,
        height=360,
    )

st.caption(
    "Data: *Public spaces – Lebanon 2023*, Impact Open Data / Government of Lebanon, "
    "published through AUB's PKGCube. Built with Streamlit and Plotly for the "
    "Visualization & Communication course, AUB, Fall 2026."
)
