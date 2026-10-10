# Part 1: polished visual system for the UG thesis deck
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---------------------------------------------------------------- palette
# deep navy base (UG gravitas)
NAVY   = RGBColor(0x0E, 0x16, 0x2A)
NAVY2  = RGBColor(0x16, 0x22, 0x3A)   # panel
NAVY3  = RGBColor(0x1E, 0x2B, 0x49)   # inner card
# accents
BLUE   = RGBColor(0x5B, 0x8D, 0xF7)   # soft blue accent (primary)
BLUE_D = RGBColor(0x3A, 0x5F, 0xBA)   # darker blue for gradient feel
GOLD   = RGBColor(0xE8, 0xB1, 0x3A)   # UG gold (warm, not harsh)
GOLD_SO= RGBColor(0xF2, 0xCF, 0x86)   # light gold
# text on dark
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT  = RGBColor(0xE2, 0xE8, 0xF2)
MUTE   = RGBColor(0x9A, 0xA6, 0xBC)
GREY   = RGBColor(0x6B, 0x77, 0x8C)
# text on light panels
DARKTX = RGBColor(0x18, 0x22, 0x33)
DARK2  = RGBColor(0x2C, 0x3A, 0x52)
RULE_L = RGBColor(0xCB, 0xD3, 0xE2)
# light slide bg
CREAM  = RGBColor(0xF6, 0xF3, 0xEC)
CREAM2 = RGBColor(0xEF, 0xEA, 0xDF)
# semantic
GREEN  = RGBColor(0x5E, 0xD2, 0xA3)
RED    = RGBColor(0xE2, 0x7A, 0x6B)
TEAL   = RGBColor(0x56, 0xCF, 0xF2)

# ---------------------------------------------------------------- geometry: 16:9
W = Inches(13.333)
H = Inches(7.5)
prs = Presentation()
prs.slide_width  = W
prs.slide_height = H
BLANK = prs.slide_layouts[6]

# ---------------------------------------------------------------- low-level
def add_slide():
    return prs.slides.add_slide(BLANK)

def set_bg(s, c):
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = c

def rect(s, x, y, w, h, c, line=None, line_w=1.0, shape=MSO_SHAPE.RECTANGLE):
    sp = s.shapes.add_shape(shape, x, y, w, h)
    sp.fill.solid()
    sp.fill.fore_color.rgb = c
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(line_w)
    sp.shadow.inherit = False
    return sp

def rrect(s, x, y, w, h, c, line=None, line_w=1.0, radius=0.08):
    """rounded rectangle; radius is fraction of min(w,h)."""
    sp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    sp.fill.solid(); sp.fill.fore_color.rgb = c
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(line_w)
    sp.shadow.inherit = False
    try:
        sp.adjustments[0] = radius
    except Exception:
        pass
    return sp

def line_h(s, x, y, w, c, thick=1.5):
    sp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, Pt(thick))
    sp.fill.solid(); sp.fill.fore_color.rgb = c
    sp.line.fill.background(); sp.shadow.inherit = False
    return sp

def vline(s, x, y, h, c, thick=1.0):
    sp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Pt(thick), h)
    sp.fill.solid(); sp.fill.fore_color.rgb = c
    sp.line.fill.background(); sp.shadow.inherit = False
    return sp

def txt(s, x, y, w, h, t, sz=18, c=WHITE, bold=False, al=PP_ALIGN.LEFT,
        anc=MSO_ANCHOR.TOP, font="Calibri", ital=False, ls=1.0, wrap=True, spacing=None):
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anc
    tf.margin_left = tf.margin_right = Pt(3)
    tf.margin_top = tf.margin_bottom = Pt(1)
    if spacing is not None:
        try:
            tf.line_spacing = spacing
        except Exception:
            pass
    p = tf.paragraphs[0]
    p.alignment = al
    p.line_spacing = ls
    r = p.add_run()
    r.text = t
    f = r.font
    f.size = Pt(sz); f.bold = bold; f.italic = ital
    f.color.rgb = c; f.name = font
    return tb

def paras(s, x, y, w, h, lines, sz=15, c=WHITE, al=PP_ALIGN.LEFT, bul=False,
          ls=1.18, gap_after=4, gap_before=0, font="Calibri", first_bold=False,
          indent=0.0, bullet_c=None, chunk_colors=None, nib=False):
    """lines: list of strings. Supports multi-color per-line via chunk_colors list.
    bullets rendered as a separate small shape for nicer look."""
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = Pt(4)
    tf.margin_top = tf.margin_bottom = Pt(2)
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = al
        p.line_spacing = ls
        p.space_after = Pt(gap_after)
        p.space_before = Pt(gap_before)
        if indent:
            try:
                p.paragraph_format.left_indent = Pt(indent)
            except Exception:
                pass
        bp = ""
        if bul:
            bp = "•  "
        elif nib:
            bp = "–  "
        r = p.add_run()
        r.text = bp + ln
        f = r.font
        f.size = Pt(sz); f.name = font
        if chunk_colors and i < len(chunk_colors) and chunk_colors[i] is not None:
            f.color.rgb = chunk_colors[i]
        else:
            f.color.rgb = c
        if i == 0 and first_bold:
            f.bold = True
    return tb

def brand_footer(s, page_no, accent=BLUE):
    line_h(s, Inches(0.5), Inches(7.02), Inches(12.33), RGBColor(0x2A,0x35,0x52), 0.75)
    txt(s, Inches(0.5), Inches(7.06), Inches(6), Inches(0.32),
        "EduRisk Predictor  •  University of Ghana", 9, GREY, ital=True)
    txt(s, Inches(11.0), Inches(7.06), Inches(1.8), Inches(0.32),
        str(page_no), 9, GREY, al=PP_ALIGN.RIGHT)

def top_bar(s, color=BLUE, h=0.10):
    rect(s, Inches(0), Inches(0), W, Inches(h), color)

def accent_tab(s, x, y, w, h, label, c=GOLD, txt_c=NAVY, sz=11):
    rrect(s, x, y, w, h, c, radius=0.5)
    txt(s, x, y, w, h, label, sz, txt_c, bold=True, al=PP_ALIGN.CENTER, anc=MSO_ANCHOR.MIDDLE)

def chip(s, x, y, w, h, label, bg, txt_c=WHITE, sz=10):
    rrect(s, x, y, w, h, bg, radius=0.5)
    txt(s, x, y, w, h, label, sz, txt_c, bold=True, al=PP_ALIGN.CENTER, anc=MSO_ANCHOR.MIDDLE)

# ---------------------------------------------------------------- constants
TITLE       = "EduRisk Predictor"
SUBTITLE    = ("An AI-Based System for Predicting University Students\u2019 Academic "
               "Performance and Assisting Lecturers and Academic Advisors in Identifying "
               "At-Risk Students Early")
STUDENT     = "[STUDENT NAME]"
IDLINE      = "(ID)"
DEGREE      = "MASTER OF PHILOSOPHY / MASTER OF SCIENCE IN COMPUTER SCIENCE"
SCHOOL      = "SCHOOL OF GRADUATE STUDIES"
DEPT        = "DEPARTMENT OF COMPUTER SCIENCE"
DATE        = "[MONTH] / [YEAR]"

# =====================================================================
# SECTION TABS (used on content slides to show which sections are covered)
# =====================================================================
def section_tabs(s, y, labels, active=None, c=BLUE, active_c=GOLD, bg=NAVY2, gap=0.12):
    """renders a row of pill tabs. active = index (or None)."""
    total = sum((Inches(0.14) if i>0 else Inches(0)) +
                Inches(0.16) + _text_w(labels[i], 10.5, c) + Inches(0.16)
                for i in range(len(labels)))
    # estimate widths
    widths = []
    for i, lab in enumerate(labels):
        wlab = _text_w(lab, 10.5, c) + Inches(0.34)
        widths.append(wlab)
    x = Inches(0.55)
    total_w = sum(widths) + Inches(0.12)*(len(labels)-1)
    # center the tab group if it fits
    if total_w < Inches(10.5):
        x = (W - total_w)/2
    for i, lab in enumerate(labels):
        w = widths[i]
        if active is not None and i == active:
            rrect(s, x, y, w, Inches(0.34), active_c, radius=0.5)
            txt(s, x, y, w, Inches(0.34), lab, 10.5, NAVY, bold=True, al=PP_ALIGN.CENTER, anc=MSO_ANCHOR.MIDDLE)
        else:
            rrect(s, x, y, w, Inches(0.34), bg, line=RGBColor(0x33,0x44,0x5C), line_w=0.75, radius=0.5)
            txt(s, x, y, w, Inches(0.34), lab, 10, MUTE, al=PP_ALIGN.CENTER, anc=MSO_ANCHOR.MIDDLE)
        x = x + w + Inches(0.12)

def _text_w(t, sz_pt, color):
    """rough text width estimate in EMU using average char width."""
    # approx avg char width at sz_pt = sz_pt * 0.5 pt; 1pt = 12700 EMU
    return int(len(t) * sz_pt * 0.55 * 12700)

# =====================================================================
# FRONT MATTER SLIDES
# =====================================================================

def slide_title(s, page_no):
    set_bg(s, NAVY)
    top_bar(s, GOLD, 0.14)
    # subtle side accent
    rect(s, Inches(0), Inches(0.14), Inches(0.10), H-Inches(0.14), BLUE_D)
    # university block
    txt(s, Inches(0.6), Inches(0.42), W-Inches(1.2), Inches(0.42),
        "UNIVERSITY OF GHANA", 22, LIGHT, bold=True, al=PP_ALIGN.CENTER)
    txt(s, Inches(0.6), Inches(0.82), W-Inches(1.2), Inches(0.34),
        "COLLEGE OF BASIC AND APPLIED SCIENCES", 13, MUTE, al=PP_ALIGN.CENTER)
    txt(s, Inches(0.6), Inches(1.06), W-Inches(1.2), Inches(0.34),
        "DEPARTMENT OF COMPUTER SCIENCE", 13, MUTE, al=PP_ALIGN.CENTER)
    # gold divider
    rect(s, Inches(5.4), Inches(1.55), Inches(2.53), Inches(0.05), GOLD)
    # TITLE word
    txt(s, Inches(0.6), Inches(1.75), W-Inches(1.2), Inches(0.3),
        "TITLE", 11, GREY, ital=True, al=PP_ALIGN.CENTER)
    # big title
    txt(s, Inches(0.5), Inches(2.05), W-Inches(1.0), Inches(1.5),
        TITLE, 50, WHITE, bold=True, al=PP_ALIGN.CENTER, ls=1.0)
    # blue accent rule
    rect(s, Inches(5.0), Inches(3.35), Inches(3.33), Inches(0.07), BLUE)
    # subtitle
    txt(s, Inches(0.8), Inches(3.5), W-Inches(1.6), Inches(1.4),
        SUBTITLE, 17, LIGHT, al=PP_ALIGN.CENTER, ls=1.4)
    # submission block
    txt(s, Inches(0.6), Inches(4.95), W-Inches(1.2), Inches(0.34),
        "A THESIS SUBMITTED TO THE " + SCHOOL + " IN", 13, MUTE, al=PP_ALIGN.CENTER)
    txt(s, Inches(0.6), Inches(5.25), W-Inches(1.2), Inches(0.34),
        "PARTIAL FULFILLMENT OF THE AWARD OF DEGREE OF " + DEGREE, 13, MUTE, al=PP_ALIGN.CENTER)
    txt(s, Inches(0.6), Inches(5.55), W-Inches(1.2), Inches(0.34),
        DEPT, 13, MUTE, al=PP_ALIGN.CENTER)
    rect(s, Inches(5.4), Inches(5.95), Inches(2.53), Inches(0.04), GOLD)
    # author
    txt(s, Inches(0.6), Inches(6.08), W-Inches(1.2), Inches(0.42),
        "BY   " + STUDENT, 20, WHITE, bold=True, al=PP_ALIGN.CENTER)
    txt(s, Inches(0.6), Inches(6.5), W-Inches(1.2), Inches(0.32),
        IDLINE, 13, MUTE, al=PP_ALIGN.CENTER)
    txt(s, Inches(0.6), Inches(6.82), W-Inches(1.2), Inches(0.3),
        DATE, 12, GREY, ital=True, al=PP_ALIGN.CENTER)
    brand_footer(s, page_no)

def slide_declaration(s, page_no):
    set_bg(s, NAVY)
    top_bar(s, BLUE, 0.10)
    txt(s, Inches(0.6), Inches(0.42), Inches(12), Inches(0.6),
        "DECLARATION", 30, WHITE, bold=True)
    line_h(s, Inches(0.6), Inches(1.06), Inches(12.1), RGBColor(0x2A,0x35,0x52), 1.0)
    txt(s, Inches(0.8), Inches(1.22), Inches(11.7), Inches(0.45),
        "I hereby declare that this thesis is a record of my own work and investigation "
        "carried out under the supervision of the Supervisor(s) detailed below.",
        14, LIGHT, ital=True, ls=1.25)
    # three cards
    bw = Inches(3.78); gap = Inches(0.22)
    x0 = (W - (3*bw + 2*gap))/2
    y0 = Inches(1.85)
    cards = [
        ("STUDENT", STUDENT),
        ("SUPERVISOR", "[SUPERVISOR NAME]"),
        ("CO-SUPERVISOR", "[CO-SUPERVISOR NAME]"),
    ]
    for i,(tag,name) in enumerate(cards):
        x = x0 + i*(bw+gap)
        rrect(s, x, y0, bw, Inches(4.05), NAVY2, radius=0.04)
        rect(s, x, y0, bw, Inches(0.08), BLUE)
        accent_tab(s, x+Inches(0.22), y0+Inches(0.24), bw-Inches(0.44), Inches(0.36),
                   tag, c=GOLD, txt_c=NAVY)
        txt(s, x+Inches(0.24), y0+Inches(0.72), bw-Inches(0.48), Inches(0.3),
            "BY", 12, MUTE, ital=True)
        line_h(s, x+Inches(0.24), y0+Inches(1.06), bw-Inches(0.48), RGBColor(0x2A,0x35,0x52),0.75)
        txt(s, x+Inches(0.24), y0+Inches(1.14), bw-Inches(0.48), Inches(0.34),
            "Name:  " + name, 14, LIGHT)
        line_h(s, x+Inches(0.24), y0+Inches(1.52), bw-Inches(0.48), RGBColor(0x2A,0x35,0x52),0.75)
        txt(s, x+Inches(0.24), y0+Inches(1.60), bw-Inches(0.48), Inches(0.3),
            "Signature:", 12, GREY)
        rect(s, x+Inches(0.24), y0+Inches(1.92), bw-Inches(0.48), Inches(0.55),
             RGBColor(0x22,0x2E,0x44))
        txt(s, x+Inches(0.3), y0+Inches(2.0), bw-Inches(0.56), Inches(0.4),
            "____________________", 13, MUTE)
        txt(s, x+Inches(0.24), y0+Inches(2.58), bw-Inches(0.48), Inches(0.3),
            "Date:", 12, GREY)
        rect(s, x+Inches(0.24), y0+Inches(2.90), bw-Inches(0.48), Inches(0.5),
             RGBColor(0x22,0x2E,0x44))
        txt(s, x+Inches(0.3), y0+Inches(2.98), bw-Inches(0.56), Inches(0.4),
            "_______________", 13, MUTE)
        txt(s, x+Inches(0.24), y0+Inches(3.55), bw-Inches(0.48), Inches(0.3),
            IDLINE, 11, GREY, ital=True)
    brand_footer(s, page_no)

def slide_abstract(s, page_no):
    set_bg(s, NAVY)
    top_bar(s, BLUE, 0.10)
    txt(s, Inches(0.6), Inches(0.42), Inches(12), Inches(0.55),
        "ABSTRACT", 28, WHITE, bold=True)
    line_h(s, Inches(0.6), Inches(0.98), Inches(12.1), RGBColor(0x2A,0x35,0x52), 1.0)
    # label + body layout: 6 rows
    lbl_w = Inches(1.1)
    body_x = Inches(1.85)
    body_w = Inches(10.6)
    rows = [
        ("CONTEXT", "Universities generate large volumes of student data \u2014 examination scores, "
         "attendance records, assignment and continuous-assessment marks, learning-management-system "
         "activity and demographics \u2014 yet many institutions still identify academically weak students "
         "only after poor examination results have occurred, when intervention can no longer prevent failure."),
        ("AIM", "To design and develop an Artificial Intelligence (AI)-based system that predicts "
         "university students\u2019 academic performance and assists lecturers and academic advisors in "
         "identifying academically at-risk students at an early stage."),
        ("METHOD", "Design and Development research methodology. A 2,550-record mid-semester snapshot was "
         "assembled and pre-processed (de-duplication, type coercion, range validation, median/mode "
         "imputation) to 2,500 usable records described by 11 features. Five classifiers \u2014 Random Forest, "
         "Decision Tree, Logistic Regression, Na\u00EFve Bayes and SVM \u2014 were compared using a stratified 80/20 "
         "split and 5-fold stratified cross-validation. The best model was embedded in a production-ready "
         "Flask web application with role-based dashboards, a REST API, CSV ingestion, rule-based "
         "intervention recommendations and an auditable intervention tracker."),
        ("RESULT", "Random Forest was selected on the strength of the best cross-validated F1 (0.833 \u00B1 0.015) "
         "and achieved 83.0% held-out accuracy with weighted precision 0.830, recall 0.830 and F1 0.829; "
         "per-class F1 was 0.850 (Low), 0.831 (Medium) and 0.768 (High). Continuous-assessment marks, "
         "previous GPA and mid-semester performance were the strongest predictors. The deployed system scored "
         "a single student in a mean of 184 ms and 1,000 students in 275 ms, and all 51 automated tests passed."),
        ("CONCLUSION", "AI-driven early-warning prediction is feasible, accurate and actionable within a "
         "university setting: the system converts routine mid-semester records into prioritised risk alerts and "
         "concrete intervention recommendations, enabling support before final examinations rather than after "
         "failure. Its accuracy depends on data quality, so it is designed as decision support for lecturers "
         "and advisors rather than a replacement for professional judgement."),
    ]
    y = Inches(1.18)
    rh = Inches(0.86)
    for label, body in rows:
        accent_tab(s, Inches(0.6), y, lbl_w, rh, label, c=BLUE, txt_c=WHITE, sz=11)
        txt(s, body_x, y+Inches(0.04), body_w, rh-Inches(0.06), body, 13, LIGHT, ls=1.2)
        y = y + rh + Inches(0.04)
    # keywords row
    ky = y + Inches(0.02)
    rrect(s, Inches(0.6), ky, Inches(12.13), Inches(0.5), NAVY3, radius=0.06)
    rect(s, Inches(0.6), ky, Inches(0.07), Inches(0.5), GOLD)
    txt(s, Inches(0.8), ky, Inches(1.2), Inches(0.5), "KEYWORDS", 12, GOLD, bold=True, anc=MSO_ANCHOR.MIDDLE)
    txt(s, Inches(2.05), ky, Inches(10.5), Inches(0.5),
        "student performance prediction; educational data mining; early-warning system; "
        "machine learning; academic risk; Random Forest", 12, LIGHT, anc=MSO_ANCHOR.MIDDLE, ls=1.1)
    brand_footer(s, page_no)

def slide_dedication(s, page_no):
    set_bg(s, NAVY)
    top_bar(s, BLUE, 0.10)
    txt(s, Inches(0.6), Inches(0.42), Inches(12), Inches(0.55),
        "DEDICATION", 28, WHITE, bold=True)
    line_h(s, Inches(0.6), Inches(0.98), Inches(12.1), RGBColor(0x2A,0x35,0x52), 1.0)
    # centered quote card
    cw = Inches(11.0); cx = (W-cw)/2
    rrect(s, cx, Inches(2.05), cw, Inches(2.35), NAVY2, radius=0.03)
    rect(s, cx, Inches(2.05), cw, Inches(0.07), GOLD)
    txt(s, cx+Inches(0.5), Inches(2.4), cw-Inches(1.0), Inches(1.9),
        "\u201CTo my loving parents, my family, and everyone who supported me through this "
        "academic journey \u2014 thank you for your prayers, your patience, and your unwavering "
        "belief in my ability to finish what I started.\u201D",
        20, LIGHT, al=PP_ALIGN.CENTER, ls=1.5, ital=True)
    txt(s, Inches(0.6), Inches(5.55), W-Inches(1.2), Inches(0.45),
        STUDENT, 16, WHITE, bold=True, al=PP_ALIGN.CENTER)
    brand_footer(s, page_no)

def slide_acknowledgement(s, page_no):
    set_bg(s, NAVY)
    top_bar(s, BLUE, 0.10)
    txt(s, Inches(0.6), Inches(0.42), Inches(12), Inches(0.55),
        "ACKNOWLEDGEMENT", 27, WHITE, bold=True)
    line_h(s, Inches(0.6), Inches(0.98), Inches(12.1), RGBColor(0x2A,0x35,0x52), 1.0)
    txt(s, Inches(0.8), Inches(1.2), Inches(11.7), Inches(0.4),
        "I wish to express my sincere gratitude to the following:", 15, LIGHT, ital=True)
    paras(s, Inches(1.0), Inches(1.75), Inches(11.3), Inches(4.2), [
        "My supervisor(s), for their expert guidance, patience, and constructive criticism "
        "throughout this research work.",
        "The Department of Computer Science, University of Ghana, for providing the academic "
        "environment and resources that made this work possible.",
        "My parents, siblings, and friends, for their love, prayers, and encouragement.",
        "Everyone who in one way or the other contributed to the success of this project.",
    ], sz=15, ls=1.5, gap_after=14)
    txt(s, Inches(0.6), Inches(6.5), Inches(11.8), Inches(0.4),
        STUDENT, 15, WHITE, bold=True, al=PP_ALIGN.RIGHT)
    brand_footer(s, page_no)

def slide_toc(s, page_no):
    set_bg(s, NAVY)
    top_bar(s, BLUE, 0.10)
    txt(s, Inches(0.6), Inches(0.42), Inches(12), Inches(0.55),
        "TABLE OF CONTENTS", 25, WHITE, bold=True)
    line_h(s, Inches(0.6), Inches(0.98), Inches(12.1), RGBColor(0x2A,0x35,0x52), 1.0)
    # two columns
    col1 = [
        ("DECLARATION", "i", True),
        ("ABSTRACT", "ii", True),
        ("DEDICATION", "iii", True),
        ("ACKNOWLEDGEMENT", "iv", True),
        ("TABLE OF CONTENTS", "v", True),
        ("LIST OF FIGURES", "vi", True),
        ("LIST OF TABLES", "vii", True),
        ("LIST OF ABBREVIATIONS", "viii", True),
        ("CHAPTER ONE  \u2014  INTRODUCTION", "1", False),
        ("1.1 Background and Motivation", "1", False),
        ("1.2 Statement of the Problem", "1", False),
        ("1.3 Scope of the Study", "1", False),
    ]
    col2 = [
        ("1.4 Research Objectives", "1", False),
        ("1.5 Research Contribution", "1", False),
        ("1.6 Organization of the Study", "1", False),
        ("CHAPTER TWO  \u2014  LITERATURE REVIEW", "2", False),
        ("2.1 Introduction", "2", False),
        ("CHAPTER THREE  \u2014  RESEARCH METHODOLOGY", "3", False),
        ("CHAPTER FOUR  \u2014  EXPERIMENTAL RESULTS AND DISCUSSIONS", "4", False),
        ("CHAPTER FIVE  \u2014  CONCLUDING REMARKS", "5", False),
        ("REFERENCES", "6", True),
    ]

    def render(col, x, lw):
        yy = Inches(1.2)
        for label, pg, emph in col:
            txt(s, x, yy, lw, Inches(0.28), label, 12, LIGHT if emph else MUTE, bold=emph, al=PP_ALIGN.LEFT, ls=1.0)
            pgx = x + lw - Inches(0.9)
            txt(s, pgx, yy, Inches(0.85), Inches(0.28), pg, 11, GREY, ital=True, al=PP_ALIGN.RIGHT)
            line_h(s, x, yy+Inches(0.29), lw, RGBColor(0x2A,0x35,0x52), 0.5)
            yy = yy + Inches(0.32)

    render(col1, Inches(0.7), Inches(5.7))
    render(col2, Inches(6.85), Inches(5.7))
    brand_footer(s, page_no)

def slide_list(s, page_no, title, items, cols=2, col_gap=0.2):
    set_bg(s, NAVY)
    top_bar(s, BLUE, 0.10)
    txt(s, Inches(0.6), Inches(0.42), Inches(12), Inches(0.55),
        title, 25, WHITE, bold=True)
    line_h(s, Inches(0.6), Inches(0.98), Inches(12.1), RGBColor(0x2A,0x35,0x52), 1.0)
    n = len(items)
    per = (n + cols - 1)//cols
    cw = (W - Inches(1.2) - col_gap*(cols-1))/cols
    for c in range(cols):
        x = Inches(0.6) + c*(cw + col_gap)
        yy = Inches(1.2)
        for it in items[c*per:(c+1)*per]:
            # split into number label + rest
            if "  " in it:
                num, rest = it.split("  ",1)
            else:
                num, rest = it, ""
            # number badge
            chip(s, x, yy, Inches(0.62), Inches(0.3), num, BLUE, txt_c=WHITE, sz=9)
            txt(s, x+Inches(0.72), yy, cw-Inches(0.8), Inches(0.45), rest, 11.5, LIGHT, ls=1.05)
            yy = yy + Inches(0.47)
    brand_footer(s, page_no)

def slide_lof(s, page_no):
    figs = [
        "Figure 1  System architecture of the proposed early-warning system",
        "Figure 2  End-to-end system workflow",
        "Figure 3  Distribution of risk levels in the training dataset",
        "Figure 4  Model comparison on the held-out test set",
        "Figure 5  Confusion matrix of the selected Random Forest model",
        "Figure 6  Top 15 feature importances of the selected model",
        "Figure 7  Login interface",
        "Figure 8  Early-warning dashboard",
        "Figure 9  Student records with risk filters",
        "Figure 10  Student detail with prediction, factors and interventions",
        "Figure 11  Model performance page",
        "Figure 12  Reports page with advisor work-list",
    ]
    set_bg(s, NAVY)
    top_bar(s, BLUE, 0.10)
    txt(s, Inches(0.6), Inches(0.42), Inches(12), Inches(0.55),
        "LIST OF FIGURES", 25, WHITE, bold=True)
    line_h(s, Inches(0.6), Inches(0.98), Inches(12.1), RGBColor(0x2A,0x35,0x52), 1.0)
    cw = Inches(5.95); gap = Inches(0.3)
    for c in range(2):
        x = Inches(0.6) + c*(cw+gap)
        yy = Inches(1.2)
        start = c*6
        for i in range(6):
            ii = start+i
            full = figs[ii]
            num, rest = (full.split("  ",1)+["",""])[:2]
            chip(s, x, yy, Inches(0.72), Inches(0.3), num, BLUE, sz=9)
            txt(s, x+Inches(0.84), yy, cw-Inches(0.92), Inches(0.45), rest, 11.5, LIGHT, ls=1.05)
            yy = yy + Inches(0.5)
    brand_footer(s, page_no)

def slide_lot(s, page_no):
    tabs = [
        "Table 1  Student data dictionary (attributes and descriptions)",
        "Table 2  Risk band definition",
        "Table 3  System development tools",
        "Table 4  Functional requirements",
        "Table 5  Non-functional requirements",
        "Table 6  Test types and scope",
        "Table 7  Dataset profile after preprocessing",
        "Table 8  Comparison of five classifiers",
        "Table 9  Per-class metrics of the selected model",
        "Table 10  Confusion matrix of the selected model",
        "Table 11  Feature importance ranking",
        "Table 12  Answers to the research questions",
        "Table 13  Automated system test results",
        "Table 14  User-acceptance test results",
        "Table 15  Performance benchmarks",
    ]
    set_bg(s, NAVY)
    top_bar(s, BLUE, 0.10)
    txt(s, Inches(0.6), Inches(0.42), Inches(12), Inches(0.55),
        "LIST OF TABLES", 25, WHITE, bold=True)
    line_h(s, Inches(0.6), Inches(0.98), Inches(12.1), RGBColor(0x2A,0x35,0x52), 1.0)
    cw = Inches(5.9); gap = Inches(0.35)
    for c in range(2):
        x = Inches(0.6) + c*(cw+gap)
        yy = Inches(1.2)
        start = c*8
        end = min(len(tabs), start+8)
        for i in range(start, end):
            label = tabs[i]
            num = label.split("  ",1)[0]
            rest = label.split("  ",1)[1] if "  " in label else label
            chip(s, x, yy, Inches(0.72), Inches(0.3), num, GOLD, txt_c=NAVY, sz=9)
            txt(s, x+Inches(0.86), yy, cw-Inches(0.95), Inches(0.45), rest, 11.5, LIGHT, ls=1.05)
            yy = yy + Inches(0.5)
    brand_footer(s, page_no)

def slide_loa(s, page_no):
    abbrs = [
        ("AI","Artificial Intelligence"),("API","Application Programming Interface"),
        ("CA","Continuous Assessment"),("CSV","Comma-Separated Values"),
        ("CV","Cross-Validation"),("DBMS","Database Management System"),
        ("EDM","Educational Data Mining"),("F1","F1 Score (harmonic mean of precision and recall)"),
        ("GPA","Grade Point Average"),("HTML","HyperText Markup Language"),
        ("LMS","Learning Management System"),("ML","Machine Learning"),
        ("NB","Na\u00EFve Bayes"),("REST","Representational State Transfer"),
        ("RF","Random Forest"),("RBAC","Role-Based Access Control"),
        ("SVM","Support Vector Machine"),("UAT","User Acceptance Testing"),
        ("WSGI","Web Server Gateway Interface"),
    ]
    set_bg(s, NAVY)
    top_bar(s, BLUE, 0.10)
    txt(s, Inches(0.6), Inches(0.42), Inches(12), Inches(0.55),
        "LIST OF ABBREVIATIONS", 24, WHITE, bold=True)
    line_h(s, Inches(0.6), Inches(0.98), Inches(12.1), RGBColor(0x2A,0x35,0x52), 1.0)
    cw = Inches(5.9); gap = Inches(0.35)
    for c in range(2):
        x = Inches(0.6) + c*(cw+gap)
        yy = Inches(1.2)
        start = c*10
        end = min(len(abbrs), start+10)
        for i in range(start, end):
            a,m = abbrs[i]
            rrect(s, x, yy, Inches(0.72), Inches(0.32), BLUE_D, radius=0.18)
            txt(s, x, yy, Inches(0.72), Inches(0.32), a, 10, WHITE, bold=True,
                al=PP_ALIGN.CENTER, anc=MSO_ANCHOR.MIDDLE)
            txt(s, x+Inches(0.84), yy+Inches(0.01), cw-Inches(0.9), Inches(0.32), m, 11, LIGHT,
                anc=MSO_ANCHOR.MIDDLE, ls=1.0)
            yy = yy + Inches(0.37)
    brand_footer(s, page_no)

# =====================================================================
# CHAPTER BANNER SLIDE (header + section tabs + one featured section)
# =====================================================================
def chapter_banner(s, ch_num, ch_title, page_no, sections=None):
    set_bg(s, NAVY)
    top_bar(s, GOLD, 0.12)
    # chapter number block
    rrect(s, Inches(0.55), Inches(0.55), Inches(1.7), Inches(1.7), GOLD, radius=0.06)
    txt(s, Inches(0.55), Inches(0.55), Inches(1.7), Inches(1.7), str(ch_num), 84,
        NAVY, bold=True, al=PP_ALIGN.CENTER, anc=MSO_ANCHOR.MIDDLE)
    txt(s, Inches(2.45), Inches(0.7), Inches(10.2), Inches(0.4),
        "CHAPTER " + str(ch_num), 13, BLUE, bold=True)
    txt(s, Inches(2.45), Inches(1.02), Inches(10.2), Inches(0.9),
        ch_title, 30, WHITE, bold=True, ls=1.0)
    line_h(s, Inches(2.45), Inches(1.85), Inches(9.8), BLUE, 1.5)
    # section tabs
    if sections:
        section_tabs(s, Inches(2.05), sections, active=0, c=BLUE)
    brand_footer(s, page_no)

# =====================================================================
# CONTENT SLIDE: section label tab + structured bullets + optional footer note
# =====================================================================
def content_slide(s, ch_num, ch_title, section_label, bullets, page_no,
                  note=None, accent=BLUE, columns=None, sizes=None, split=None):
    """
    bullets: list of strings. Each becomes a bullet line.
    columns: if int k>1, split bullets into k columns (approx equal).
    sizes: optional list of sizes per bullet (for emphasis).
    split: optional list of (section_title) markers; a subheading line is rendered.
    """
    set_bg(s, NAVY)
    top_bar(s, accent, 0.10)
    # chapter mini-header (top right)
    rrect(s, Inches(9.4), Inches(0.42), Inches(3.4), Inches(0.46), NAVY2, radius=0.1)
    txt(s, Inches(9.5), Inches(0.42), Inches(3.2), Inches(0.46),
        f"CH.{ch_num}  \u2022  {ch_title}", 10, MUTE, al=PP_ALIGN.RIGHT, anc=MSO_ANCHOR.MIDDLE)
    # section label tab (left)
    accent_tab(s, Inches(0.55), Inches(0.42), Inches(4.3), Inches(0.46),
               section_label, c=accent, txt_c=NAVY, sz=11)
    line_h(s, Inches(0.55), Inches(1.0), Inches(12.2), RGBColor(0x2A,0x35,0x52), 1.0)
    # body
    if columns and columns > 1:
        _content_columns(s, bullets, columns, accent)
    else:
        _content_single(s, bullets, accent, sizes)
    if note:
        txt(s, Inches(0.6), Inches(6.55), Inches(12), Inches(0.35),
            note, 10.5, GREY, ital=True)
    brand_footer(s, page_no, accent)

def _content_single(s, bullets, accent, sizes=None):
    y = Inches(1.16)
    x = Inches(0.7); w = Inches(11.95)
    vline(s, Inches(0.53), Inches(1.14), Inches(5.5), accent, 2.0)
    for i, ln in enumerate(bullets):
        if y > Inches(6.8): break
        sz = sizes[i] if sizes and i < len(sizes) else 14
        col = LIGHT; bold = False
        if _is_heading(ln):
            col = GOLD_SO if accent==GOLD else BLUE_SO; bold = True
        paras(s, x, y, w, Inches(1.2), [ln], sz=sz, c=col, bul=False, ls=1.22,
              gap_after=(6 if _is_heading(ln) else 3), first_bold=bold)
        y = y + _line_count(ln, sz)*Inches(0.245) + Inches(0.05)

BLUE_SO = RGBColor(0x9D, 0xC2, 0xF5)

def _is_heading(ln):
    s = ln.strip()
    if not s or len(s) > 85: return False
    if s[0].isdigit() and len(s)>1 and s[1]=='.': return True
    if s.startswith("RQ") or s.startswith("FR") or s.startswith("NFR"): return True
    if s.startswith("(a)") or s.startswith("(b)") or s.startswith("(c)") or s.startswith("(d)") or s.startswith("(e)"): return True
    if s.startswith("\u2022") or s.startswith("\u2013") or s.startswith("-") or s.startswith("   "): return True
    return False

def _line_count(ln, sz):
    cpl = int(11.7 / (sz*0.50/72.0))
    if cpl < 8: cpl = 8
    return max(1, int(len(ln)/cpl) + (1 if (";" in ln or ln.count(" ")>cpl*0.85) else 0))

def _content_columns(s, bullets, ncols, accent):
    line_h_in = 0.235
    body_bottom = Inches(6.62)
    cw = (W - Inches(1.25) - Inches(0.3)*(ncols-1))/ncols
    xs = [Inches(0.6) + i*(cw+Inches(0.3)) for i in range(ncols)]
    ys = [Inches(1.16) for _ in range(ncols)]
    for ln in bullets:
        approx = _line_count(ln, 13)
        needed = approx*Inches(line_h_in) + Inches(0.06)
        # place in column with most room (lowest ys)
        ci = min(range(ncols), key=lambda i: ys[i])
        if ys[ci] + needed > body_bottom:
            # this bullet won't fit anywhere at this size; try smaller size or stop
            # try sz=12 if sz=13 doesn't fit in the emptiest column
            approx2 = _line_count(ln, 12)
            needed2 = approx2*Inches(0.22) + Inches(0.05)
            ci = min(range(ncols), key=lambda i: ys[i])
            if ys[ci] + needed2 > body_bottom:
                break
            sz = 12
            c = LIGHT; b = False
            if _is_heading(ln): c = GOLD_SO; b = True
            hh2 = approx2*Inches(0.225) + Inches(0.1)
            paras(s, xs[ci], ys[ci], cw-Inches(0.12), hh2, [ln], sz=sz, c=c,
                  bul=False, ls=1.18, gap_after=(5 if _is_heading(ln) else 3), first_bold=b)
            ys[ci] = ys[ci] + needed2
        else:
            c = LIGHT; b = False
            if _is_heading(ln): c = GOLD_SO; b = True
            hh = approx*Inches(0.245) + Inches(0.1)
            paras(s, xs[ci], ys[ci], cw-Inches(0.12), hh, [ln], sz=13, c=c,
                  bul=False, ls=1.2, gap_after=(6 if _is_heading(ln) else 4), first_bold=b)
            ys[ci] = ys[ci] + needed
    # column divider lines
    for i in range(1, ncols):
        xv = Inches(0.6) + i*(cw+Inches(0.3)) - Inches(0.15)
        vline(s, xv, Inches(1.2), Inches(5.4), RGBColor(0x2A,0x35,0x52), 1.0)

# =====================================================================
# "SECTION GROUP" SLIDE : covers multiple sections with mini-headings
# =====================================================================
def section_group_slide(s, ch_num, ch_title, section_labels, bullets, page_no,
                        accent=BLUE, note=None):
    """
    One slide covering a group of sections.
    section_labels: list of short labels like ["3.9 Functional Req.", "3.10 Non-Functional Req."]
    bullets: list of strings; sections baked into bullets as headings.
    """
    set_bg(s, NAVY)
    top_bar(s, accent, 0.10)
    # chapter mini-header
    rrect(s, Inches(9.0), Inches(0.42), Inches(3.8), Inches(0.46), NAVY2, radius=0.1)
    txt(s, Inches(9.1), Inches(0.42), Inches(3.6), Inches(0.46),
        f"CHAPTER {ch_num}", 11, BLUE, bold=True, al=PP_ALIGN.RIGHT, anc=MSO_ANCHOR.MIDDLE)
    # section tabs
    if section_labels:
        section_tabs(s, Inches(0.42), section_labels, active=0, c=accent)
    line_h(s, Inches(0.55), Inches(0.95), Inches(12.2), RGBColor(0x2A,0x35,0x52), 1.0)
    # body: multi-column if many bullets, else single
    if len(bullets) > 14:
        _content_columns(s, bullets, 2, accent)
    else:
        y = Inches(1.12)
        for ln in bullets:
            sz = 13.5
            col = LIGHT
            bold = False
            is_head = (len(ln) < 75 and (ln[:3].strip().rstrip(".").isdigit()
                      or ln.startswith("RQ") or ln.startswith("FR") or ln.startswith("NFR")
                      or ln.startswith("(a)") or ln.startswith("(b)") or ln.startswith("(c)")
                      or ln.startswith("(d)") or ln.startswith("(e)") or ln.startswith("\u2022")
                      or ln.startswith("–") or ln.startswith("-") or ln.startswith("   ")
                      or ln.startswith("1.") or ln.startswith("2.") or ln.startswith("3.")
                      or ln.startswith("4.") or ln.startswith("5.") or ln.startswith("6.")
                      or ln.startswith("7.") or ln.startswith("8.") or ln.startswith("9.")))
            if is_head:
                col = GOLD_SO
                bold = True
            paras(s, Inches(0.7), y, Inches(11.95), Inches(0.5), [ln], sz=sz, c=col,
                  bul=False, ls=1.2, gap_after=7 if is_head else 4, first_bold=bold)
            approx = max(1, int(len(ln)/(95 if sz>=14 else 120)) + (1 if ";" in ln or ln.count(" ")>16 else 0))
            y = y + Inches(0.25)*approx + Inches(0.05)
            if y > Inches(6.5):
                break
    if note:
        txt(s, Inches(0.6), Inches(6.55), Inches(12), Inches(0.35),
            note, 10.5, GREY, ital=True)
    brand_footer(s, page_no, accent)

# section_labels tab overflow guard: keep short
def _short_label(lab, maxc=20):
    return lab if len(lab) <= maxc else lab[:maxc-1].rstrip()+"…"
