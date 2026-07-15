# Accessibility Guide

Clarion exists to reduce communication barriers in Slack. This document
explains the accessibility features Clarion provides, who benefits from them,
and how they are implemented.

---

## Who Clarion Helps

Clarion is designed for real people with real communication needs:

| User group | Challenge | Clarion's response |
|---|---|---|
| People with dyslexia | Dense text, long sentences, and unfamiliar words increase cognitive load | Simplifies to short sentences and common words |
| People with ADHD | Walls of text are difficult to prioritise and scan | Extracts key points, decisions, and action items |
| Non-native English speakers | Idioms, jargon, and culture-specific metaphors are opaque | Replaces idioms with literal alternatives; offers translation |
| People who are blind or have low vision | Images shared in Slack have no alt-text | Generates screen-reader-ready alt-text and full descriptions |
| Screen-reader users | Slack's interface has gaps in accessibility | Provides text-based summaries and descriptions |
| Late joiners and returning colleagues | Long threads require reading everything from the start | Produces structured catch-up digests |
| Newcomers and junior teammates | Internal jargon and acronyms feel alienating | Defines terms using live workspace context |
| Message authors | Jargon in drafts can exclude teammates | Reviews drafts and suggests inclusive alternatives |

---

## Features and How They Work

### Text Simplification

**What it does**: Rewrites corporate jargon and complex sentences into plain
language, preserving every decision, owner, deadline, and action item.

**Reading levels**:
- **Grade 5** — short sentences, common everyday words, one idea per sentence
- **Grade 8** — plain language, no jargon, slightly more complex structure
- **Plain** — clear and easy to follow for a busy adult (default)
- **Concise** — only the essential information, minimal detail

**Jargon replaced** (examples):
`leverage` → `use` · `bandwidth` → `capacity` · `circle back` → `follow up` ·
`synergy` → `working together` · `move the needle` → `make progress` ·
`deliverable` → `output` · `ideate` → `brainstorm`

**Cognitive accessibility principle**: Research shows that people with dyslexia
and ADHD process shorter sentences (under 20 words) significantly more easily.
Clarion breaks long compound sentences into individual ideas.

---

### Image Alt-Text Generation

**What it does**: Generates two levels of description for uploaded images:
1. A concise alt-text sentence (under 125 characters) for screen readers
2. A thorough visual description covering layout, content, text transcription,
   and contextual meaning

**Why Slack images lack alt-text**: When users upload images to Slack, the
platform does not prompt for alt-text. This means screen-reader users receive
no information about images by default — a significant barrier in visual
workplaces.

**WCAG alignment**: This feature addresses WCAG 2.1 Success Criterion 1.1.1
(Non-text Content), which requires a text alternative for all non-text content.

**Best practice**: Alt-text should describe the *meaning and purpose* of an
image, not just what it contains. A chart showing Q3 revenue growth is not
described well as "a bar chart" — it needs to say what the data shows.

---

### Thread Catch-Up Digest

**What it does**: Converts a long thread into a structured plain-language
summary with four sections: decisions made, who needs to do what, key dates
and deadlines, and what is still being worked out.

**Who benefits most**: People returning from leave or sick days, those who
joined a project mid-way, and anyone with ADHD who finds it difficult to
re-engage with a long, unstructured thread.

**Plain language principle**: The digest uses consistent structure and predictable
formatting so users know exactly where to look for each type of information.
Structure reduces cognitive load.

---

### Jargon and Acronym Definitions

**What it does**: Defines internal shorthand using live workspace context from
the Real-Time Search API. Definitions are warm, inclusive, and treat the reader
as intelligent but unfamiliar — not as someone who should already know.

**Why this matters**: Jargon creates insider/outsider dynamics. Newcomers and
non-native speakers often feel too embarrassed to ask what common acronyms mean.
Clarion removes this barrier privately, in a DM.

**Tone principle**: Definitions should never make the reader feel they should
already know this. The phrase "Everyone deserves conversations that are easy
to understand" reflects this.

---

### Inclusive Language Check

**What it does**: Reviews a draft message for jargon, idioms, unexplained
acronyms, and phrasing that may be unclear to non-native speakers, neurodivergent
readers, or newcomers. Suggests complete sentence rewrites, not just word swaps.

**Coaching tone**: Clarion addresses the writer as someone trying to communicate
well — not as someone who has done something wrong. The goal is to help, not
to police language.

**Common barriers detected**:
- Sports metaphors (unavailable to many non-native speakers): `move the needle`,
  `boil the ocean`
- Initialisms that aren't globally known: `ASAP`, `EOD`, `WFH`, `TL;DR`
- Tech / business jargon: `leverage`, `bandwidth`, `synergy`, `circle back`

---

## WCAG Considerations

Clarion addresses several Web Content Accessibility Guidelines (WCAG) success
criteria, adapted to the Slack workplace context:

| WCAG Criterion | How Clarion helps |
|---|---|
| **1.1.1 Non-text Content** | Generates alt-text for images that have none |
| **3.1.5 Reading Level** | Simplifies text to the user's chosen reading level |
| **3.1.3 Unusual Words** | Defines jargon and acronyms in context |
| **3.1.4 Abbreviations** | Expands abbreviations (EOD, ASAP, WFH, etc.) |
| **3.2.4 Consistent Identification** | Clarion's response format is always consistent |

---

## Inclusive Language Principles

Clarion's design follows these core principles:

1. **No condescension** — removing barriers does not mean dumbing things down.
   The goal is equal access, not simplified thinking.

2. **Preserve meaning** — accessibility without accuracy is worthless. Every
   decision, date, and action item must survive simplification intact.

3. **Private by default** — accessibility needs are personal. Clarion delivers
   results via DM whenever possible (shortcuts always DM; mentions reply in
   thread so the simplified version is available to all who need it).

4. **Warm tone** — language about accessibility should make people feel
   included, not labelled. Clarion avoids clinical or bureaucratic language.

5. **Offline resilience** — Clarion must help everyone even when the AI is
   unavailable. Rule-based fallbacks ensure the tool never returns nothing.

---

## Cognitive Accessibility Design

Clarion's own responses are written following cognitive accessibility best
practices:

- **Consistent structure** — every digest has the same four sections, always
  in the same order
- **Short sentences** — Clarion's own output uses the same plain-language rules
  it applies to user content
- **Clear headers** — emoji headers (📌 ✅ 👤 📅 ❓) provide visual anchors
  that benefit users with ADHD
- **No buried ledes** — the most important information comes first
- **No meta-commentary** — Clarion does not start responses with "Sure!" or
  "Great question!" — it gets straight to the point
