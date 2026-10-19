---
name: Derivatives Pricing Dashboard
description: Black-Scholes prices and Greeks set as a live worked example from a quant textbook, printed in reverse on a black page.
colors:
  ground: "#0a0b0d"
  field: "#14130f"
  ink: "#ebe6dc"
  muted: "#a69f93"
  rule: "#3b3731"
  field-border: "#7a7368"
  spot: "#8db2f0"
  error: "#f0a39a"
  ramp-0: "#0f1520"
  ramp-1: "#1c3561"
  ramp-2: "#3d6bc0"
  ramp-3: "#9fc0f5"
  ramp-4: "#e8f0ff"
  cell-ink-light: "#ffffff"
  cell-ink-dark: "#000000"
typography:
  display:
    fontFamily: "STIX Two Text, Times New Roman, serif"
    fontSize: "2.25rem"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  title:
    fontFamily: "STIX Two Text, Times New Roman, serif"
    fontSize: "1.15rem"
    fontWeight: 600
  body:
    fontFamily: "STIX Two Text, Times New Roman, serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "lnum, tnum"
  caption:
    fontFamily: "STIX Two Text, Times New Roman, serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.5
  axis:
    fontFamily: "STIX Two Text, Times New Roman, serif"
    fontSize: "0.8rem"
    fontWeight: 400
rounded:
  none: "0"
spacing:
  gap: "0.9rem"
  cell-y: "0.38rem"
  margin-pad: "2.25rem 1.5rem"
  gutter: "3rem"
  gutter-phone: "1rem"
components:
  input-field:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "0.45rem 0.6rem"
  booktabs-cell:
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "0.38rem 0.9rem"
  booktabs-unit:
    textColor: "{colors.muted}"
    typography: "{typography.body}"
  caption-block:
    textColor: "{colors.ink}"
    typography: "{typography.caption}"
  notes-block:
    textColor: "{colors.muted}"
    typography: "{typography.caption}"
  ranges-toggle:
    rounded: "{rounded.none}"
    size: "2.75rem"
  heatmap-cell:
    typography: "{typography.axis}"
---

# Design System: Derivatives Pricing Dashboard

## Overview

**Creative North Star: "Textbook Plates, Printed in Reverse"**

The page is a worked example from a quantitative finance textbook: numbered display equations, a booktabs table labelled "Table 1.", captioned figures labelled "Figure 1." and "Figure 2.", and a notes section, all set in one book serif. It is rendered dark because the user pinned "keep ui black", so the plate is inverted: warm off-white ink on a near-black ground, with no paper color anywhere. The page explicitly rejects the metric-tile dashboard. There are no cards, tiles, badges, or panels; structure comes from typographic rules, captions, and the margin.

Density is set by the book, not the app. The text block is capped near 52rem for equations, the table, and figures, and prose holds a 68ch measure. Inputs live in a left margin column like marginalia, separated by one hairline. Every number is set in lining tabular figures, so columns align by digit. True minus signs (U+2212), scientific notation as a mantissa times ten to a superscript power, and upright capital Greek against italic lowercase follow mathematical typesetting convention.

Motion is minimal and functional. Inputs ease their border color in 150ms, the results fade to 55% opacity while a new quote is in flight, and the phone ranges toggle collapses its plus into a minus. Every transition turns off under reduced motion.

**Key Characteristics:**
- One serif family (STIX Two Text) for everything, with KaTeX for equations, set to the same serif.
- Near-black ground, warm off-white ink, one pale spot blue, one salmon error color.
- Booktabs rules (1.5px top and bottom, 1px under the header, 1px midrule) are the main structural device.
- Square corners everywhere; no cards, no elevation.
- Numbered equations, numbered tables and figures, bold run-in labels ("Table 1.", "Model.") as in a printed text.

## Colors

A restrained palette: warm ink on near-black with a single cool spot blue, which also anchors the one sequential ramp used in the figures.

### Primary
- **Plate Spot Blue** (spot): The only accent. It marks focus rings, focused input borders, and links, and it is the hue the heatmap ramp climbs toward. Selection uses a deep tint of it. It never fills a surface or a button.

### Tertiary
- **Erratum Salmon** (error): Reserved for failure. It colors the status line when a quote fails or an input is empty, and the border of an invalid input. Nothing decorative uses it.

### Neutral
- **Reverse-Plate Black** (ground): The page itself, under every section. It also shows through the 1px gaps between heatmap cells and serves as the knockout halo around the heatmap marker.
- **Inset Field Black** (field): A barely warmer black used only as the input fill, so fields read as inset without a box.
- **Warm Plate Ink** (ink): All primary text, headings, table figures, bold run-in labels, and the heavy booktabs rules (top, header, and bottom).
- **Graphite Annotation** (muted): Secondary text: the lede, the "where" clause, units, symbols, the check column, axis labels, footnotes, notes, and the credit line (7.5:1 on ground).
- **Hairline Umber** (rule): Light structural lines: the margin column divider, the table midrule, the credit's top rule, and the input stroke at rest.
- **Control Stroke** (field-border): The resting stroke for inputs and the toggle, 3.97:1 on the field fill; hover steps it to muted.

### Heatmap ramp
- **Ramp 0 to 4** (ramp-0 through ramp-4): A five-stop sequential ramp from a blue-black just above ground to an almost-white blue, linearly interpolated per cell and drawn as the vertical legend. It is the only multi-hue-step color in the system and appears only in figures.
- **Cell ink** (cell-ink-light, cell-ink-dark): Heatmap cell values are pure white or pure black, chosen per cell by WCAG contrast against its fill. The worst case on the ramp is 4.58:1.

### Named Rules
**The One Spot Rule.** The spot blue is the only accent. It signals focus, links, and figure data; it never fills a control or decorates a heading.

**The Contrast-Picked Cell Ink Rule.** Text on a data fill is pure black or pure white, whichever has the higher WCAG contrast with that fill. It is computed, never hand-picked, and must clear 4.5:1 on every ramp position.

**The Error Is Only Error Rule.** Salmon appears only when something failed or is missing.

## Typography

**Display Font:** STIX Two Text (with Times New Roman, serif)
**Body Font:** STIX Two Text (with Times New Roman, serif)
**Math:** KaTeX 0.18.10, with its roman and math-italic remapped to STIX Two Text; KaTeX_Main supplies only the infinity sign, which no STIX Two Text subset carries.

**Character:** A single scholarly book serif doing every job, the way a typeset textbook would. Weight 600 and size carry the hierarchy; italic carries mathematical variables and the axis titles.

STIX Two Text is pinned at @fontsource/stix-two-text@5.3.0 with Latin (400, 400 italic, 600), Latin-ext (400, for the dagger), and Greek (400, 400 italic) subsets.

### Hierarchy
- **Display** (600, 2.25rem desktop, 1.85rem phone, 1.15 line height, -0.01em): The page title only.
- **Title** (600, 1.15rem desktop, 1.05rem phone): Margin section headings ("Inputs", "Heatmap ranges").
- **Body** (400, 1rem, 1.5 line height, lining tabular numerals): Table figures, the lede (slightly larger at 1.05rem, muted, 68ch), equation text, and the "where" clause (italic, muted).
- **Caption** (400, 0.95rem): Table and figure captions with bold run-in labels, notes, input labels, and the status line. Prose measures cap at 68ch.
- **Axis** (400, 0.8rem): Heatmap axis labels and legend; cell values sit just below at 0.72rem (0.7rem on phones).

### Named Rules
**The Textbook Setting Rule.** Set mathematics as mathematics: lowercase variables and Greek italic, capital Greek upright, true minus signs, superscript exponents, and lining tabular figures in every number.

**The Run-In Label Rule.** Tables, figures, and notes are introduced by a bold run-in label in ink ("Table 1.", "Figure 2.", "Model.") followed by plain sentence text. There are no separate headings above plates.

## Layout

Desktop is a two-column page: a 17rem margin column on the left holding the input form (sticky at 2.25rem from the top), and a text column on the right capped at 64rem with 3rem gutters. Inside the text column, equations, Table 1, and figures share a 52rem block so equation numbers sit flush right with the table edge, while prose holds 68ch. Figures sit two-up with a 2.5rem gap, collapsing to one column below 900px.

At 720px and below, the order becomes title, inputs, plates. The margin becomes a band ruled above and below, with inputs in a three-column grid (0.6rem gap) and the heatmap ranges folded behind a 44px toggle. Gutters drop to 1rem. The table tightens its cell padding, moves units under the quantity name, and swaps the long check header for a short one.

The form rhythm is a single 0.9rem gap; label-to-field spacing is 0.3rem.

## Elevation & Depth

The system is flat. There is no elevation and no shadow anywhere; depth is expressed only by the slightly warmer input fill against the ground, and by rules. The single box-shadow in the build is a 1.5px ground-colored knockout stroke around the heatmap's crosshair marker, which separates the ink cross from bright cells. It is a halo, not a shadow, and casts no offset.

### Named Rules
**The Flat Plate Rule.** Surfaces never lift. Separate things with rules, space, and captions, not with shadows, cards, or fills.

## Shapes

Square corners throughout (radius 0) on inputs, the toggle, heatmap cells, and the legend. Lines come in two weights only: 1.5px for the heavy booktabs rules and the drawn marker and toggle bars, and 1px for everything else. The ranges toggle's plus and minus and the heatmap crosshair are drawn from two CSS bars, not glyphs or icons.

## Components

### Inputs / Fields
Quiet, inset, and typeset like the page.
- **Style:** Field-black fill, 1px field-border stroke (3.97:1 on the fill), square corners, 0.45rem by 0.6rem padding, body type inherited. Labels sit above with the variable symbol in italic ("Spot price *S*").
- **Hover / Focus:** Stroke steps to muted on hover; on focus the stroke turns spot blue and the 2px spot focus ring sits flush (offset 0). Border color eases over 150ms.
- **Error:** Invalid (empty) fields take an error-salmon stroke, and the status line names the field.
- **Note:** Control strokes (inputs and the phone ranges toggle) use field-border, never rule: rule on field is 1.57:1, below the 3:1 non-text floor. Rule stays for hairlines that separate content.

### Booktabs Table (signature)
The core plate. Header row and last row are bounded by 1.5px ink rules, the header underlined by a 1px ink rule, and a 1px rule-colored midrule separates paired call/put rows from Greeks shared by both, which center across the two value columns. Figures are right-aligned; quantity, unit, and check columns are left-aligned, with units and the check column in muted. A dagger footnote in muted at 0.85rem explains the parity row. The table scrolls horizontally within its own wrapper if needed.

### Numbered Equations (signature)
KaTeX display math in STIX Two Text, numbered with right-aligned tags (1) to (3), each ending with today's computed value, followed by an italic muted "where" clause listing the inputs.

### Heatmap Figure (signature)
A 10 by 10 grid of square-cornered cells (aspect 1.25) separated by 1px ground gaps, filled from the ramp, with contrast-picked black or white values. Axis titles are italic in ink ("σ", "Spot S"); tick labels and the vertical gradient legend labels are muted at axis size. An ink crosshair with a ground halo marks the current inputs. Each figure carries a caption with a bold "Figure n." run-in label.

### Navigation
None. The page is a single plate with no nav.

### Ranges Toggle (phone only)
A 2.75rem square, transparent, 1px field-border stroke, square corners, containing a muted plus drawn from two 1.5px bars; the vertical bar scales to zero when expanded. Hover steps the stroke to muted.

### Stale State
While a quote is in flight, equations, table, and figures fade to 0.55 opacity over 150ms and return when the response renders.

## Do's and Don'ts

### Do:
- **Do** set every number in lining tabular figures with true minus signs, and exponents as superscripts (8.6×10<sup>−7</sup>).
- **Do** introduce every table and figure with a bold run-in label ("Table 1.", "Figure 3.") inside its caption.
- **Do** separate content with booktabs rules: 1.5px ink for top and bottom, 1px ink under the header, 1px rule for midrules and dividers.
- **Do** keep the spot blue for focus, links, and figure data only.
- **Do** pick text on any data fill as pure black or pure white by WCAG contrast, clearing 4.5:1.
- **Do** keep prose at 68ch and plates at 52rem.
- **Do** disable every transition under prefers-reduced-motion.

### Don't:
- **Don't** build metric tiles, cards, or panels; the page is a plate, not a dashboard grid.
- **Don't** add elevation shadows; the only permitted shadow-like device is a zero-offset ground halo that knocks a mark out of a data field.
- **Don't** round corners on any control, cell, or container.
- **Don't** introduce a second display or UI typeface; STIX Two Text sets everything, including KaTeX output.
- **Don't** use icon fonts or glyph icons; draw marks from CSS bars as the toggle and crosshair do.
- **Don't** use salmon for anything but a failure or missing input.
- **Don't** switch to a light ground; the dark page is a user-pinned commitment.
