---
name: FinSolve Assistant
description: Role-scoped answers from FinSolve's own documents, set like a page of the annual report.
colors:
  page: "#ffffff"
  panel: "#f6f7f9"
  panel-strong: "#eef0f4"
  line: "#e3e6ec"
  line-strong: "#cdd2db"
  navy: "#14213d"
  navy-hover: "#22335a"
  navy-soft: "#e8ecf4"
  on-navy: "#ffffff"
  on-navy-muted: "#b6c0d4"
  text: "#1b2230"
  text-muted: "#545d70"
  text-faint: "#5d6578"
  ink-finance: "#1b6f80"
  ink-finance-soft: "#e3f1f4"
  ink-marketing: "#b45a14"
  ink-marketing-soft: "#fbeee2"
  ink-hr: "#6a4c93"
  ink-hr-soft: "#efe9f6"
  ink-engineering: "#2b7449"
  ink-engineering-soft: "#e4f2ea"
  ink-general: "#556074"
  ink-general-soft: "#eceef2"
  declined: "#8a5a12"
  declined-soft: "#fdf5e6"
  declined-line: "#ecd5a8"
  error: "#b42318"
  error-soft: "#fdecea"
typography:
  display:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "clamp(28px, 2.6vw, 36px)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.015em"
  headline:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "30px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.015em"
  question:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "24px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Source Sans 3, -apple-system, Segoe UI, sans-serif"
    fontSize: "18px"
    fontWeight: 700
    lineHeight: 1.35
  prose:
    fontFamily: "Source Sans 3, -apple-system, Segoe UI, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.65
    fontFeature: "lnum"
  body:
    fontFamily: "Source Sans 3, -apple-system, Segoe UI, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
    fontFeature: "lnum"
  label:
    fontFamily: "Source Sans 3, -apple-system, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 700
    lineHeight: 1.35
  meta:
    fontFamily: "Source Sans 3, -apple-system, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.35
  figure:
    fontFamily: "Source Sans 3, -apple-system, Segoe UI, sans-serif"
    fontWeight: 700
    fontFeature: "tnum, lnum"
  note-marker:
    fontFamily: "Source Sans 3, -apple-system, Segoe UI, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 0
    fontFeature: "tnum"
rounded:
  sm: "4px"
  md: "8px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "5": "24px"
  "6": "32px"
  "7": "48px"
  "8": "64px"
components:
  top-bar:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.on-navy}"
    height: "60px"
    padding: "0 32px"
  button-primary:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.on-navy}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    height: "44px"
    padding: "0 18px"
  button-primary-hover:
    backgroundColor: "{colors.navy-hover}"
    textColor: "{colors.on-navy}"
  button-primary-disabled:
    backgroundColor: "{colors.panel-strong}"
    textColor: "{colors.text-faint}"
  button-secondary:
    backgroundColor: "{colors.page}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    height: "36px"
    padding: "0 14px"
  input-field:
    backgroundColor: "{colors.page}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    height: "44px"
    padding: "0 12px"
  ink-tag:
    backgroundColor: "{colors.ink-general-soft}"
    textColor: "{colors.ink-general}"
    typography: "{typography.meta}"
    rounded: "{rounded.sm}"
    padding: "1px 8px"
  note-marker:
    backgroundColor: "{colors.ink-general-soft}"
    textColor: "{colors.ink-general}"
    typography: "{typography.note-marker}"
    rounded: "{rounded.sm}"
    padding: "1px 5px"
  note-marker-active:
    backgroundColor: "{colors.ink-general}"
    textColor: "{colors.on-navy}"
  note-row:
    rounded: "{rounded.md}"
    padding: "10px"
  note-row-lit:
    backgroundColor: "{colors.ink-general-soft}"
  callout-declined:
    backgroundColor: "{colors.declined-soft}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "16px 18px"
  callout-error:
    backgroundColor: "{colors.error-soft}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "16px 18px"
  access-rail:
    backgroundColor: "{colors.panel}"
    width: "256px"
    padding: "32px 24px"
  sources-panel:
    backgroundColor: "{colors.panel}"
    width: "320px"
    padding: "32px 24px"
---

# Design System: FinSolve Assistant

## Overview

**Creative North Star: "Annual Report"**

Every answer is set like a page of FinSolve's own annual report: a white page under a deep navy masthead, the reader's question as a serif page heading, the answer in a plain workhorse sans with its figures set bold, tabular and navy, and a superscript note number after every claim that leads to a named source document in the margin. The system's job is trust at a desk in daylight. It is light, quiet and dense in the way a well-made report is dense: hairline rules, one cool panel step, small corners, no ornament that does not carry information.

Colour is a filing system, not decoration. Each data category owns one fixed ink with a soft tint, and that ink is the department's identity everywhere it appears: the access rail, the demo-role tags on sign-in, the note markers in an answer, and the numbered rows of the Sources panel. Navy belongs to the shell and to the one primary action on a screen. Amber and red appear only when an answer did not happen.

The world deliberately rejects two neighbours: the grey-bubble AI chat clone (no bubbles, no avatars, no alternating sides; the thread is a sequence of report sections) and the dark trading-terminal costume this project previously wore (no dark ground, no monospace UI, no glowing accents).

**Key Characteristics:**
- White page, cool #f6f7f9 side panels, navy shell band and primary actions.
- One fixed ink per department, handed to any element through `--ink` / `--ink-soft`.
- Superscript note markers glued to the preceding word, keyed to a numbered Sources panel.
- Serif reserved for page-heading text (the asked question, the empty-state prompt, the sign-in headline); everything else Source Sans 3.
- Figures in answers are bold, tabular, lining and navy.
- Depth from hairlines and the panel colour step; one soft shadow, under the ask bar.
- One motion moment: the answer setting in.

## Colors

A daylit report palette: neutral white and cool grey paper, one deep navy voice, five department inks, and two state colours that appear only on failure.

### Primary
- **Report Navy** (`navy`): the 60px top band, the Ask and Sign in buttons, figures inside answers, the current question heading, the sign-in and empty-state headlines, link colour, caret colour, the focus ring, table header rules and the pending sweep. **Navy Hover** (`navy-hover`) is its only hover step; **Navy Wash** (`navy-soft`) fills a hovered example prompt and a demo role that is signing in.
- **On Navy** (`on-navy`) and **Muted On Navy** (`on-navy-muted`): text on the band; the muted step carries secondary words ("Assistant" in the wordmark, "Signed in as").

### Secondary: department inks
One ink and one soft tint per data category. The pair is the department, wherever it is drawn.
- **Finance Teal** (`ink-finance` / `ink-finance-soft`)
- **Marketing Orange** (`ink-marketing` / `ink-marketing-soft`)
- **HR Violet** (`ink-hr` / `ink-hr-soft`)
- **Engineering Green** (`ink-engineering` / `ink-engineering-soft`)
- **General Slate** (`ink-general` / `ink-general-soft`): also the fallback when a source's department cannot be determined.

Inks are never hard-coded per component. A single helper (`inkStyle(category)`) sets `--ink` and `--ink-soft` on an element to the matching department tokens; component CSS only ever reads `var(--ink)` and `var(--ink-soft)`.

### Tertiary: states
- **Declined Amber** (`declined`, `declined-soft`, `declined-line`): the "Not answered" callout title, fill and border, and the "Not answered" status in the session list.
- **Error Red** (`error`, `error-soft`): the failed-request and session-expired callouts, the sign-in error, the "Failed" session status.

### Neutral
- **Page White** (`page`): the reading surface, inputs, secondary buttons, the active session row.
- **Panel Grey** (`panel`): the access rail and Sources panel, pre blocks, demo-role row hover.
- **Panel Strong** (`panel-strong`): inline code chips, session-row hover, disabled Ask button.
- **Hairline** (`line`) and **Strong Hairline** (`line-strong`): dividers and table rows; input, ask-bar, example and secondary-button strokes, scrollbar thumbs.
- **Report Ink** (`text`), **Muted** (`text-muted`), **Faint** (`text-faint`): body text; secondary copy, descriptions and table headers; placeholders, hints and "no access" departments.

Browser surfaces are tuned to the world: selection is a pale navy wash with navy text, the caret is navy, scrollbars are thin with a strong-hairline thumb.

### Named Rules
**The One Ink Rule.** A department has exactly one ink and one tint, and they mean that department everywhere: rail swatch, sign-in tag, note marker, note number. Never pick an ink for its hue, and never let a department ink stand for a state.

**The Navy Voice Rule.** Navy is the shell and the single primary action per view. A second navy-filled button on the same screen is a mistake.

**The Quiet State Rule.** Amber and red are reserved for answers that did not happen. A successful answer carries no state colour at all; its department inks do the talking.

## Typography

**Display Font:** Source Serif 4, weight 600 only (with Georgia, serif)
**Body Font:** Source Sans 3, weights 400 / 600 / 700 (with -apple-system, Segoe UI, sans-serif)
**Code:** the platform monospace stack (ui-monospace, SFMono-Regular, Menlo), inside answers only.

Both families are self-hosted through @fontsource; no other weights ship.

**Character:** A sturdy text serif sets what is being asked; a workhorse grotesque carries everything that answers, explains or controls. The pairing reads like a report's section heading over its body copy.

### Hierarchy
- **Display** (serif 600, clamp 28 to 36px, 1.2, -0.015em, max 18ch, balanced): the sign-in headline only.
- **Headline** (serif 600, 30px / 26px under 860px, 1.2): the empty-state prompt, which stands in for the first question.
- **Question** (serif 600, 24px / 21px under 860px, 1.25, -0.01em, balanced): each asked question as the heading of its exchange; navy when it is the current exchange, report ink otherwise.
- **Title** (sans 700, 18px, 1.35): headings the model writes inside an answer. Sign-in's "Or sign in as a demo role" is the sans 600 20px sibling.
- **Prose** (sans 400, 17px, 1.65, max 68ch): answer text; ledes on sign-in and the empty state also run at 17px muted.
- **Body** (sans 400, 16px, 1.6, lining figures by default): all other UI copy.
- **Label** (sans 700, 15px): panel titles ("Your access", "Sources", "This session"); form labels are the 600 sibling.
- **Meta** (sans 400 to 600, 13px): department descriptions, note file paths, table headers, ink tags, the ask hint.
- **Figure** (sans 700, tabular + lining, navy): money and percentages detected in an answer's prose.
- **Note marker** (sans 700, 12px, tabular, line-height 0): superscript source numbers.

### Named Rules
**The Asked Question Rule.** Serif is for page-heading text a person reads as "the question on this page": the asked question, the empty-state prompt, the sign-in headline. Nothing else is ever serif: not panel titles, not buttons, not headings inside answers.

**The Figures Are Set Rule.** Lining numerals everywhere; tabular lining numerals wherever figures sit in a column or carry weight (answer figures, tables, note numbers).

**The No Kicker Rule.** Headings stand alone. No small uppercase or tracked label sits above a heading to announce it.

## Layout

The chat shell is a full-height column: the 60px navy band, then a three-column grid of access rail (256px), thread (fluid), and Sources panel (320px). The rail and panel scroll independently on Panel Grey with a hairline against the page; the thread scrolls on white with its content held to a 720px measure (prose further capped at 68ch). The ask bar is anchored at the bottom of the thread column at the same 720px width, followed by a one-line faint hint.

Exchanges are separated by a hairline and 32px of vertical space; the first sits directly under the thread's top padding. The empty state sits a little lower (10vh, clamped 24 to 96px) so the prompt reads as the page's opening.

Sign-in is a white page under the same band: a centred 1120px container with two equal columns 64px apart (the sign-in form, max 400px, on the left; the demo-role list on the right), stacking to one column under 860px.

Spacing follows an 8px-based scale (4, 8, 12, 16, 24, 32, 48, 64). A few component-internal values sit between steps (6px gaps in tags and callout titles, 10px note-row padding, 18px callout and button side padding); these are optical adjustments, not new steps.

### Responsive behaviour
- **Under 1180px:** the Sources panel disappears and each answer carries its own source list inline beneath it, set off by a hairline; the rail narrows to 240px.
- **Under 860px:** the rail becomes a wrapping strip of compact department chips above the thread (title, descriptions and note hidden), the grid becomes a single column whose tracks can shrink so wide tables scroll inside themselves, and thread and ask-bar side padding drop to 16px.
- **Under 640px:** the top band's padding tightens to 16px.
- **Under 560px:** "Signed in as" and the "Sign out" word hide; the role name and the sign-out icon remain.
- **Sign-in under 480px:** demo-role rows stack the role name above its department tags.

## Elevation & Depth

The system is flat paper. Depth comes from two things only: hairline rules (`line`, `line-strong`) and the single tonal step from Page White to Panel Grey that separates the margins from the page. Selection inside lists (the lit note, the active session row, a "no access" swatch) is drawn with a 1px inset outline, not a lift.

### Shadow Vocabulary
- **Ask-bar lift** (`box-shadow: 0 1px 2px rgba(20, 33, 61, 0.06), 0 10px 28px -14px rgba(20, 33, 61, 0.22)`): the one elevated object, the place where the reader writes.
- **Focus halo** (`box-shadow: 0 0 0 3px rgba(20, 33, 61, 0.12)` on the ask bar, `0.14` on sign-in inputs): a navy ring paired with a navy border when a text field holds focus. It is a focus indicator, not elevation.

### Named Rules
**The One Lift Rule.** Only the ask bar casts a shadow. Panels, callouts, notes and buttons sit on the page.

**The Report Focus Rule.** Keyboard focus is a 2px navy outline offset 2px with a 4px corner, globally; on the navy band it turns white. Text fields swap that for a navy border plus a soft navy halo so there is never a double ring.

## Shapes

Small, practical corners. Gently squared controls and containers (`rounded.md`, 8px): buttons, inputs, callouts, example prompts, note rows, pre blocks, session rows. Tighter corners (`rounded.sm`, 4px) on small inline things: ink tags, note markers, code chips, the focus ring. A handful of optical one-offs follow the same small-corner logic: the 10px ask bar, 6px controls on the navy band, the 5px note-number square, the 3px department swatch.

Fully round shapes appear only where a strip of compact chips needs them: the department chips in the under-860px rail strip, the pending sweep bar's ends and scrollbar thumbs.

Borders are 1px hairlines everywhere except the 2px navy rule under a report table's header row.

## Components

### Top bar
The masthead. A 60px Report Navy band, the wordmark on the left ("FinSolve" in 700, "Assistant" in muted 400, 18px, baseline-aligned), controls on the right. In chat it carries the role pill (white at 10% on navy, 6px corners, "Signed in as" muted) and a ghost Sign out button (30% white hairline, 6px corners, 34px tall, white 10% fill on hover, icon plus word). Sign-in shows the band with the wordmark only.

### Buttons
- **Shape:** gently squared (8px).
- **Primary:** Report Navy fill, white 600 text, 44px tall with 18px sides for Ask (icon plus word), 46px full-width for Sign in. One per view.
- **Hover / Focus:** fill shifts to Navy Hover over 150ms on the house ease; focus is the global navy ring.
- **Disabled:** Ask goes Panel Strong with faint text; Sign in goes a greyed navy (#9aa3b5).
- **Secondary (callout action):** white, strong-hairline stroke, 36px, 600 text, optional 16px icon; the stroke turns navy on hover. Used for Try again and Sign in again.
- **Example prompt:** a full-width white row with a strong hairline, 8px corners, left-aligned body text; hover takes a navy stroke and Navy Wash fill.

### Department ink tag
- **Style:** the department's soft tint behind its ink, 13px 600 text, 4px corners, 1 to 2px by 8px padding.
- **Where:** each demo role on sign-in lists the departments it reads as tags; the "Not answered" callout lists the signed-in role's readable departments as the same tags.

### Inputs / Fields
- **Sign-in fields:** 44px, white, strong-hairline stroke, 8px corners, 12px side padding, 600 15px label above. Hover darkens the stroke slightly; focus replaces the outline with a navy border and soft navy halo.
- **Ask bar:** one white 10px-cornered container holding a borderless 17px input and the Ask button; the container carries the focus treatment (navy border, halo) and the only lift. Placeholder copy names the departments the role can read.

### Navigation: access rail
The left margin, titled "Your access", lists all five departments every time. Each row: a 12px swatch in the department ink, the name (600) over a 13px description, and a state icon at the right; rows are divided by hairlines. Readable departments show a check in their ink; others show an empty, outlined swatch, a lock, and faint text, with a visually hidden "can read" / "no access" for assistive tech. A muted note under the list explains that unticked departments are never searched. Under 860px the rail becomes a wrapping row of white, fully round chips, swatch plus name plus state icon.

### Callouts (answer states)
Each state replaces the answer under the question heading.
- **Pending:** a 56px hairline track with a navy segment sweeping across it, beside muted "Searching the documents your role can read…". The panel says sources will appear when the answer arrives.
- **Answered:** the answer prose, then (under 1180px) its inline source list.
- **Not answered:** one amber callout for every decline (Declined Soft fill, Declined Line stroke, 8px corners). Title in Declined Amber with the neutral info icon; body explains that the topic may be uncovered or may sit in a department the role cannot read (the backend does not say which); a next step; then the role's readable departments as ink tags. The panel reads "No sources: this question wasn't answered."
- **Error:** Error Soft fill with a pale red stroke, title in Error Red with the alert icon, the message, and a secondary Try again button. When the session has expired the title becomes "Session expired" and the action becomes Sign in again.

### Report tables, code and prose
Answers are Markdown rendered with GitHub-flavoured tables, raw HTML (for line breaks the model puts in cells), then sanitised.
- **Tables:** full width inside a horizontally scrolling wrapper; 15px tabular lining figures; header cells 13px 700 muted over a 2px navy rule; body rows separated by hairlines, top-aligned. Cells align right only when the Markdown alignment row asks for it; otherwise left.
- **Inline code:** Panel Strong chip, 4px corners, monospace at 0.88em.
- **Code blocks:** Panel Grey, hairline stroke, 8px corners, 14px monospace, scrolling horizontally.
- **Figures:** money and percentage figures in prose are bolded, tabular and navy. Detection runs only on prose, never inside the model's own code spans or blocks, and figure tokens carry an invisible marker so genuine code stays code.
- **Other prose:** answer headings at the Title level, blockquotes with a strong-hairline left rule in muted text, hairline horizontal rules.

### Superscript notes and the Sources panel (signature)
The model's inline `[Source: file]` citations are removed from the prose and replaced by superscript note numbers, numbered in order of first citation; a repeated document reuses its number.
- **Marker:** inline (never an inline block) and non-breaking, glued to the word it follows, so it can never strand at the start of a line. Department tint behind department ink, 12px 700 tabular, 4px corners; on hover or focus it fills solid with the ink and white text.
- **Sources panel:** the right margin, titled "Sources", lists the numbered notes for the shown answer. Each row: a 24px ink square with the white number, the document title (a humanised filename, 15px 600) over "Department · filename" in 13px muted. Documents retrieved but never cited appear below a muted "Also consulted" sub-label with a document icon in their ink and no number; they never receive a number they did not earn.
- **Interaction:** hovering a marker previews that answer's sources in the panel and lights the note; leaving restores the current answer. Focusing or clicking a marker commits that answer as current, lights the note and scrolls it into view (in the panel when visible, otherwise in the inline list).
- **Lit note:** the row takes its department tint with a 1px inset outline in its ink.
- **This session:** below the sources, once there are two or more questions, a list of each question (two-line clamp) with its status word; the current one is white with an inset strong hairline. Clicking scrolls the thread to that exchange.

### Iconography
A small authored set on one 24px grid, 1.75 stroke, round caps and joins, drawn in `currentColor`: lock, check, info, arrow up, sign out, document, alert, retry. Default 18px; 16 to 17px in dense rows. Icons are always paired with words or hidden from assistive tech.

### Motion
One moment and one indicator, both on the house ease-out-expo (`cubic-bezier(0.16, 1, 0.3, 1)`).
- **Set-in:** a new answer fades up from 20% opacity and a 6px drop over 520ms.
- **Pending sweep:** the navy segment crosses its track every 1.1s while searching.
- State transitions on controls run 150 to 200ms on colour, border and inset outline only. Reduced-motion preferences collapse animations and transitions.

## Do's and Don'ts

### Do:
- **Do** hand a department its colour only through `inkStyle(category)` and read `var(--ink)` / `var(--ink-soft)` in CSS.
- **Do** show all five departments in access views, readable ones in ink with a check, others faint with a lock.
- **Do** number a source only when the answer cites it; list retrieved but uncited documents under "Also consulted".
- **Do** keep note markers inline and non-breaking against the preceding word.
- **Do** set the asked question in Source Serif 4 600 and everything that answers in Source Sans 3.
- **Do** set figures bold, tabular, lining and navy in prose, and tabular in tables.
- **Do** separate with hairlines and the Panel Grey step; keep corners at 4px or 8px.
- **Do** give every failure state a next step: rephrase or ask the owning department, Try again, or Sign in again.

### Don't:
- **Don't** use chat bubbles, avatars or left/right message alignment.
- **Don't** use a dark ground, monospace UI text or glowing accents; that is the terminal world this system replaced.
- **Don't** reuse a department ink for a state, a brand accent or decoration.
- **Don't** claim why an answer was declined; the backend does not say, so the single "Not answered" callout covers both causes.
- **Don't** put a kicker or eyebrow label above a heading.
- **Don't** add shadows to panels, callouts, notes or buttons; the ask bar is the one lifted object.
- **Don't** set panel titles, buttons or in-answer headings in the serif.
- **Don't** add a second motion moment beyond the answer set-in and the pending sweep.
