"""Build the Word document submitted on Moodle (snapshots, justifications, problems, AI use)."""

import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

NAVY, MUTED = RGBColor(0x10, 0x23, 0x3F), RGBColor(0x66, 0x70, 0x85)

doc = Document()
for s in doc.sections:
    s.left_margin = s.right_margin = Inches(0.9)
    s.top_margin = s.bottom_margin = Inches(0.8)

normal = doc.styles["Normal"]
normal.font.name, normal.font.size = "Calibri", Pt(11)
normal.paragraph_format.space_after, normal.paragraph_format.line_spacing = Pt(8), 1.12
for name, size in (("Title", 22), ("Heading 1", 14), ("Heading 2", 12)):
    st = doc.styles[name]
    st.font.name, st.font.size, st.font.bold, st.font.color.rgb = "Calibri", Pt(size), True, NAVY


def para(text, italic=False, color=None):
    """Paragraph where **bold** markers are rendered as bold runs."""
    p = doc.add_paragraph()
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if not part:
            continue
        run = p.add_run(part.strip("*"))
        run.bold = part.startswith("**")
        run.italic = italic
        if color:
            run.font.color.rgb = color
    return p


def picture(path):
    doc.add_picture(path, width=Inches(6.6))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


doc.add_heading("Streamlit assignment — Public spaces in Lebanon", level=0)
para("Mariam Ismail · Visualization & Communication · AUB, Fall 2026", italic=True, color=MUTED)

doc.add_heading("Links", level=1)
para("App (Streamlit Community Cloud): [paste your app link here after deploying]")
para("GitHub repository: [paste your repository link here]")

doc.add_heading("Snapshot of the page", level=1)
para("The national view. The governorate control is set to All Lebanon, so the district control is "
     "disabled and the first chart is at governorate level.")
picture("app_snapshot.png")
para("The drill-down. Selecting Mount Lebanon fills the district control with that governorate's "
     "districts only, and the first chart switches to district level. Both charts and all four "
     "metrics follow the selection.")
picture("app_snapshot_drilldown.png")

doc.add_heading("Design justifications", level=1)

doc.add_heading("Control 1 — Governorate (single-select dropdown)", level=2)
para("**User question:** “Is the national picture true where I live?” The single national figure "
     "(32.8% of towns have a public park) hides a range from Akkar at 23.6% to Beqaa at 55.2%, so a "
     "reader needs to move from the country to one region.")
para("**Why this widget:** there are seven governorates in the survey, and only one can be the scope "
     "at a time. Pills or a segmented control would put all seven on screen permanently, competing "
     "with the charts for attention and wrapping awkwardly on a laptop. A multiselect would let a "
     "reader merge, for example, Akkar and Beqaa into a single bar — a combination with no "
     "administrative meaning. The dropdown enforces exactly one scope, which is what a drill-down needs.")
para("**Course concepts — reducing clutter and providing context:** the control collapses seven "
     "options into one line of the sidebar. Because filtering can mislead, the chosen scope is "
     "restated in three places: the sidebar caption (“378 of 1,137 towns in view”), the metrics "
     "row (with the gap to the national average), and the dashed national-average line, which stays at "
     "its national value no matter how far the reader drills in.")

doc.add_heading("Control 2 — Districts (multiselect, options driven by control 1)", level=2)
para("**User question:** “Inside this region, is coverage even, or is one district pulling the "
     "average?” This is the natural follow-up, and it only makes sense after a governorate is chosen.")
para("**How the two are linked:** the options in this control are generated from the governorate "
     "selected above, never from the full list of districts. Choosing North offers only Batroun, "
     "Bsharri, Miniyeh–Danniyeh, Tripoli and Zgharta. The first chart also changes level with the "
     "selection: governorate bars for All Lebanon, district bars once a governorate is picked. While "
     "the scope is All Lebanon the control is disabled with the hint “Pick a governorate first”, "
     "and for Akkar — which has no district recorded anywhere in the published data — it is "
     "disabled with an explanation instead of showing an empty list.")
para("**Why this widget:** comparing two or three districts against each other is the point, so the "
     "control must allow several selections at once, which rules out a selectbox. Individual checkboxes "
     "would mean one widget per district and would not reset when the governorate changes.")
para("**Course concepts — focusing attention and honest comparison:** deselecting districts removes "
     "bars but never rescales the reference line, so a narrowed view is still read against the same "
     "national yardstick rather than a flattering local one.")

doc.add_heading("What broke and how I fixed it", level=1)

doc.add_heading("1. District selections survived a change of governorate", level=2)
para("**What happened:** with one multiselect reused across governorates, Streamlit kept the previous "
     "widget state. Selecting Tripoli and Zgharta under North and then switching to South left the app "
     "holding districts that do not exist in South, so the charts came back empty.")
para("**The fix:** give the multiselect a key that includes the governorate, "
     "key=f’districts::{governorate}’. Streamlit then treats it as a different widget per "
     "governorate, so the list resets to that governorate's own districts. This is also why the control "
     "is disabled, rather than merely empty, for All Lebanon and for Akkar.")

doc.add_heading("2. The national-average label collided with the bars", level=2)
para("**What happened:** the dashed national-average line is annotated with its value. Positioned at "
     "the top of the line, the label was clipped by the edge of the plot in the national view, and in "
     "the Mount Lebanon view it landed on top of the longest bar's value label.")
para("**The fix:** move the annotation to the bottom of the line, where both views have empty space, "
     "and add top margin to the chart. I checked both states before accepting the fix.")

doc.add_heading("3. Windows console encoding broke the Streamlit CLI", level=2)
para("**What happened:** running ‘streamlit skills’ failed with a UnicodeEncodeError, because the "
     "default Windows console encoding (cp1252) cannot print the warning symbol the command emits.")
para("**The fix:** run it with PYTHONIOENCODING=utf-8. A second Windows-specific issue appeared right "
     "after: the project-scoped install uses symlinks, which require Developer Mode, so the installer "
     "fell back to a global install — which works the same way for this project.")

doc.add_heading("AI-use statement", level=1)
para("[Review and edit this section so it matches exactly what you did.]", italic=True, color=MUTED)
para("**Tool used:** Claude (Claude Code), as a coding assistant throughout this assignment.")
para("**What it was used for:** installing Streamlit and its official agent skills; writing "
     "streamlit_app.py and data_prep.py, including the two linked controls and both Plotly charts; "
     "drafting the page text, the on-page design justifications and this document; running headless "
     "tests of the app and capturing the snapshots; and setting up the Git repository.")
para("**What I checked and changed:** I supplied the dataset, the cleaning logic and the two insights "
     "from my earlier Plotly assignment, and I verified every figure in the app against that notebook "
     "(1,137 towns, 32.8% national coverage, Mount Lebanon 25.9%, non-reporting towns 16.2%). I "
     "corrected the assistant where it was wrong: it first described eight governorates when the survey "
     "contains seven, because Beirut has no towns in this dataset. I also had it replace a cluttered "
     "district list with a control that stays disabled until a governorate is chosen. I reviewed all "
     "text on the page and rewrote parts of it in my own words before submitting.")

doc.add_heading("Notes on the data", level=1)
for item in [
    "Coverage always means the share of towns, never the share of people: the survey has no population "
    "figures and no geometry.",
    "The published refArea field mixes governorates and districts. Towns with no district recorded are "
    "labelled “District not specified” instead of being assigned one by guesswork.",
    "Missing ratings are shown as their own category (“Not reported”), never dropped — that "
    "category carries the second insight.",
    "The source CSV is double-encoded (ZahlÃ© → Zahlé) and several column names carry "
    "trailing spaces; both are handled in data_prep.py.",
]:
    doc.add_paragraph(item, style="List Bullet")

out = "Streamlit_Assignment_Mariam_Ismail.docx"
doc.save(out)
print("saved", out)
