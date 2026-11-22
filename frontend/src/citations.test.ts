// Citation parsing and decline detection: the code that turns the model's
// inline [Source: …] citations into numbered notes. Every case here is a shape
// the model has actually produced, including ones that broke the UI before.
import { describe, expect, it } from "vitest";
import { annotate, docTitle, FIGURE_MARK, isDecline, NOTE_MARK } from "./citations";

const D = "/app/data";
const ENG = [`${D}/engineering/engineering_master_doc.md`];
const FIN = [`${D}/finance/financial_summary.md`, `${D}/finance/quarterly_financial_report.md`];

/** The note-group tokens left in the markdown, e.g. ["§1,2"]. */
const noteTokens = (markdown: string) =>
  [...markdown.matchAll(/`(§[\d,]+)`/g)].map((m) => m[1]);

describe("annotate", () => {
  it("merges back-to-back citations into one group (the §1``§2 bug)", () => {
    const r = annotate(
      "The data layer includes PostgreSQL. [Source: engineering_master_doc.md – 2. System Architecture > 2.1 Overview][Source: engineering_master_doc.md – 2. System Architecture > 2.2 High-Level Architecture]",
      ENG,
    );
    expect(noteTokens(r.markdown)).toEqual([`${NOTE_MARK}1,2`]);
    expect(r.markdown).not.toContain("``");
  });

  it("keeps section paths as the note's section, not part of the file name", () => {
    const r = annotate("X [Source: engineering_master_doc.md – 2. System Architecture > 2.1 Overview].", ENG);
    expect(r.notes).toHaveLength(1);
    expect(r.notes[0]).toMatchObject({
      n: 1,
      file: "engineering_master_doc.md",
      title: "Engineering master doc",
      section: "2. System Architecture › 2.1 Overview",
      category: "engineering",
    });
  });

  it("never lists a cited document again under 'also consulted'", () => {
    const r = annotate("X [Source: engineering_master_doc.md – 2.1 Overview].", ENG);
    expect(r.consulted).toEqual([]);
  });

  it("lists retrieved but uncited documents as consulted, without a number", () => {
    const r = annotate("Revenue was $9.4 billion [Source: financial_summary.md].", FIN);
    expect(r.notes.map((n) => n.file)).toEqual(["financial_summary.md"]);
    expect(r.consulted.map((n) => n.file)).toEqual(["quarterly_financial_report.md"]);
    expect(r.consulted[0].n).toBe(0);
  });

  it("handles 【】 and (Sources: a; b) shapes", () => {
    const a = annotate("Leave is 12 days 【Source: employee_handbook.md】.", [`${D}/general/employee_handbook.md`]);
    expect(a.notes[0].category).toBe("general");
    const b = annotate("Revenue grew (Sources: financial_summary.md; quarterly_financial_report.md).", FIN);
    expect(noteTokens(b.markdown)).toEqual([`${NOTE_MARK}1,2`]);
  });

  it("matches a citation that names a document by title instead of file", () => {
    const r = annotate("Leave is 12 days [Source: Employee Handbook > Leave Policies].", [
      `${D}/general/employee_handbook.md`,
    ]);
    expect(r.notes[0]).toMatchObject({ file: "employee_handbook.md", section: "Leave Policies" });
  });

  it("reuses a note number when the same source is cited twice", () => {
    const r = annotate("A [Source: financial_summary.md]. B [Source: financial_summary.md].", FIN);
    expect(r.notes).toHaveLength(1);
    expect(noteTokens(r.markdown)).toEqual([`${NOTE_MARK}1`, `${NOTE_MARK}1`]);
  });

  it("keeps a figure and the next citation as separate tokens", () => {
    // "$9.4 billion" is wrapped as a figure; the citation right after it must
    // not merge into the same code span.
    const r = annotate("Revenue was $9.4 billion (Sources: financial_summary.md).", FIN);
    expect(r.markdown).toContain(`\`${FIGURE_MARK}$9.4 billion\``);
    expect(noteTokens(r.markdown)).toEqual([`${NOTE_MARK}1`]);
    expect(r.markdown).not.toMatch(/``§/);
  });

  it("leaves the model's own code untouched", () => {
    const r = annotate("Run `deploy-prod` on port 8080:\n\n```bash\nkubectl scale --replicas=50%\n```", []);
    expect(r.markdown).toContain("`deploy-prod`");
    expect(r.markdown).toContain("kubectl scale --replicas=50%");
    expect(r.markdown).not.toContain(FIGURE_MARK + "50%");
  });
});

describe("isDecline", () => {
  it.each([
    "I don't have that information.",
    "I don't have access to that information.",
    "  I don’t have that information  ", // curly apostrophe, stray whitespace
  ])("treats the backend's own decline %j as not answered", (answer) => {
    expect(isDecline(answer)).toBe(true);
  });

  it("does not hide a real answer that merely contains the phrase", () => {
    expect(isDecline("I don't have Q4 detail, but Q1 revenue was $2.1 billion.")).toBe(false);
    expect(isDecline("I don't have a reliable figure for that: I can only see a few matching records.")).toBe(false);
  });
});

describe("docTitle", () => {
  it("turns file names into readable titles", () => {
    expect(docTitle("quarterly_financial_report.md")).toBe("Quarterly financial report");
    expect(docTitle("hr_data.csv")).toBe("HR data");
    expect(docTitle("marketing_report_q3_2024.md")).toBe("Marketing report Q3 2024");
  });
});
