// Turns the model's own inline citations into numbered notes. The model cites
// in several shapes, all handled here:
//   [Source: quarterly_financial_report.md]
//   【Source: employee_handbook.md】
//   (Sources: a.md; b.md)
//   [Source: engineering_master_doc.md – 2. System Architecture > 2.1 Overview]
// Numbering comes only from what the answer actually cites (one note per
// document + section). Documents the backend retrieved but the answer never
// cites are listed separately as "also consulted", never given a number they
// didn't earn.
import { isCategory, type Category } from "./roles";

export interface Note {
  n: number;
  file: string;
  title: string;
  section?: string;
  category?: Category;
}

export interface AnnotatedAnswer {
  /** Markdown with each citation group replaced by one `§1,2` inline-code token
   *  and figures marked with FIGURE_MARK. */
  markdown: string;
  notes: Note[];
  consulted: Note[];
}

const CITATION = /\s?(?:\[|【|\()\s*Sources?\s*:\s*([^\]】)]+?)\s*(?:\]|】|\))/gi;
const FILE = /[\w.-]+\.(?:md|csv|pdf|txt|docx?)/gi;
const FIGURE = /(?:₹|\$)\s?[\d,]+(?:\.\d+)?\s?(?:billion|million|thousand|B|M|K)?|\b\d+(?:\.\d+)?%/g;

/** Prefix that marks an inline-code token as a figure we emphasised, so real
 *  code spans in an answer (common in Engineering answers) stay code. */
export const FIGURE_MARK = "⁣";

/** Prefix of the single token that stands for one citation group. */
export const NOTE_MARK = "§";

/** Fenced blocks and inline code spans: left exactly as the model wrote them. */
const CODE_SPAN = /(```[\s\S]*?```|`[^`\n]*`)/;

const WORD_CASE: Record<string, string> = { hr: "HR", q1: "Q1", q2: "Q2", q3: "Q3", q4: "Q4" };

export function fileName(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

/** "quarterly_financial_report.md" -> "Quarterly financial report". */
export function docTitle(file: string): string {
  const words = file.replace(/\.[a-z0-9]+$/i, "").split(/[_\-\s]+/).filter(Boolean);
  return words
    .map((w, i) => WORD_CASE[w.toLowerCase()] ?? (i === 0 ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
}

/** Sources arrive as paths under data/<category>/, so the parent folder is the department. */
function categoryOf(path: string): Category | undefined {
  const parts = path.split(/[\\/]/);
  const folder = parts[parts.length - 2];
  return folder && isCategory(folder) ? folder : undefined;
}

const normalise = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "");

/** Trim the separators models put between a filename and its section. */
function cleanSection(text: string): string | undefined {
  const s = text.replace(/^[\s–—:,;|>›-]+|[\s–—:,;|>›-]+$/g, "").replace(/\s+/g, " ");
  return s && !/^(and|&)$/i.test(s) ? s.replace(/\s*>\s*/g, " › ") : undefined;
}

interface Cited {
  file: string;
  section?: string;
}

/** Split one citation's text into (file, section) pairs. */
function parseCitation(text: string, sources: string[]): Cited[] {
  const matches = [...text.matchAll(FILE)];
  if (matches.length > 0) {
    return matches.map((m, i) => {
      const start = (m.index ?? 0) + m[0].length;
      const end = i + 1 < matches.length ? (matches[i + 1].index ?? text.length) : text.length;
      return { file: m[0], section: cleanSection(text.slice(start, end)) };
    });
  }
  // No filename: the model named a document by title ("Employee Handbook").
  // Match each piece against the retrieved documents' titles.
  return text
    .split(/[;,]|\band\b/)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      const hit = sources.find((s) => {
        const t = normalise(docTitle(fileName(s)));
        const p = normalise(part);
        return p.startsWith(t) || t.startsWith(p);
      });
      if (!hit) return { file: part };
      const rest = part.slice(docTitle(fileName(hit)).length);
      return { file: fileName(hit), section: cleanSection(rest) };
    });
}

export function annotate(answer: string, sources: string[]): AnnotatedAnswer {
  const notes: Note[] = [];
  const pathFor = (file: string) =>
    sources.find((s) => fileName(s).toLowerCase() === file.toLowerCase());

  const withMarkers = answer.replace(CITATION, (_match, inner: string) => {
    const numbers = parseCitation(inner, sources).map(({ file, section }) => {
      const key = `${file.toLowerCase()}|${(section ?? "").toLowerCase()}`;
      const existing = notes.find((x) => `${x.file.toLowerCase()}|${(x.section ?? "").toLowerCase()}` === key);
      if (existing) return existing.n;
      const path = pathFor(file);
      const note: Note = {
        n: notes.length + 1,
        file,
        title: /\.[a-z0-9]+$/i.test(file) ? docTitle(file) : file,
        section,
        category: path ? categoryOf(path) : undefined,
      };
      notes.push(note);
      return note.n;
    });
    const unique = [...new Set(numbers)];
    return unique.length ? `\`${NOTE_MARK}${unique.join(",")}\`` : "";
  });

  // Back-to-back citations ("[Source: a][Source: b]") become one group, `§1,2`:
  // two adjacent `x``y` code tokens would otherwise merge into a single
  // broken span, since a double backtick never closes a single one.
  const groupPair = new RegExp(`\`${NOTE_MARK}([\\d,]+)\`\\s*\`${NOTE_MARK}([\\d,]+)\``);
  let grouped = withMarkers;
  for (let m = groupPair.exec(grouped); m; m = groupPair.exec(grouped)) {
    const merged = [...new Set(`${m[1]},${m[2]}`.split(","))].join(",");
    grouped = grouped.replace(m[0], `\`${NOTE_MARK}${merged}\``);
  }

  const citedFiles = new Set(notes.map((x) => x.file.toLowerCase()));
  const consulted = [...new Set(sources.map(fileName))]
    .filter((file) => !citedFiles.has(file.toLowerCase()))
    .map((file) => ({ n: 0, file, title: docTitle(file), category: categoryOf(pathFor(file) ?? "") }));

  // Emphasise figures only in prose: never inside the model's own code, and
  // never inside the note tokens inserted above.
  // Any two code tokens that end up touching (a figure right before a note,
  // "$9.4 billion(Sources: …)") are kept apart by a word joiner: it separates
  // the spans for the markdown parser without allowing a line break.
  const parts = grouped
    .split(CODE_SPAN)
    .map((part, i) => (i % 2 === 1 ? part : part.replace(FIGURE, (m) => `\`${FIGURE_MARK}${m}\``)));
  const markdown = parts.reduce(
    (out, part) => (out.endsWith("`") && part.startsWith("`") ? `${out}\u2060${part}` : out + part),
    "",
  );
  return { markdown, notes, consulted };
}

// The backend declines in two phrasings ("I don't have access to that
// information." from its own short-circuit, "I don't have that information."
// from the model). Neither says *why*, so the UI can't honestly tell an
// off-topic question from a role boundary; it presents one "not answered"
// state that explains both possibilities.
const DECLINES = ["i don't have access to that information", "i don't have that information"];

export function isDecline(answer: string): boolean {
  // Whole-answer match only: a grounded answer that merely contains "I don't
  // have" ("I don't have Q4 detail, but Q1–Q3 were…") is still an answer.
  const normalised = answer.trim().toLowerCase().replace(/’/g, "'").replace(/[.!\s]+$/, "");
  return DECLINES.includes(normalised);
}
