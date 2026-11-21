import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";
import TopBar from "../components/TopBar";
import Icon from "../components/Icon";
import { askQuestion, ApiError } from "../api/client";
import { getToken, decodeToken, clearToken } from "../auth";
import { ALL_CATEGORIES, allowedCategories, type Category } from "../roles";
import { DEPARTMENTS, inkStyle, roleLabel } from "../departments";
import { annotate, isDecline, FIGURE_MARK, NOTE_MARK, type AnnotatedAnswer, type Note } from "../citations";
import { EXAMPLE_QUESTIONS } from "../exampleQuestions";
import { useSlow } from "../useSlow";
import styles from "./Chat.module.css";

type Status = "pending" | "answered" | "declined" | "error";

interface Exchange {
  id: number;
  question: string;
  status: Status;
  answer?: string;
  annotated?: AnnotatedAnswer;
  error?: string;
  expired?: boolean;
}

interface Highlight {
  id: number;
  n: number;
}

let nextId = 1;

const STATUS_CLASS: Record<Status, string> = {
  pending: "statusPending",
  answered: "statusAnswered",
  declined: "statusDeclined",
  error: "statusError",
};

const STATUS_TEXT: Record<Status, string> = {
  pending: "Searching",
  answered: "Answered",
  declined: "Not answered",
  error: "Failed",
};

export default function Chat() {
  const navigate = useNavigate();
  const token = getToken();
  const role = token ? decodeToken(token)?.role : undefined;
  const readable = role ? allowedCategories(role) : [];

  const [question, setQuestion] = useState("");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [highlight, setHighlight] = useState<Highlight | null>(null);
  // Hovering a marker previews its answer's sources; it never changes which
  // answer is current, so a passing pointer can't leave the panel showing
  // sources for an answer the reader isn't on.
  const [previewId, setPreviewId] = useState<number | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const threadEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const active = exchanges.find((ex) => ex.id === activeId) ?? exchanges[exchanges.length - 1];
  const shown = exchanges.find((ex) => ex.id === previewId) ?? active;

  // Follow the newest exchange both when it's asked and when its answer lands
  // (the block grows then), so the live answer never sits behind the ask bar.
  const latest = exchanges[exchanges.length - 1];
  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [exchanges.length, latest?.status]);

  function signOut() {
    clearToken();
    navigate("/login");
  }

  function update(id: number, patch: Partial<Exchange>) {
    setExchanges((prev) => prev.map((ex) => (ex.id === id ? { ...ex, ...patch } : ex)));
  }

  async function run(id: number, text: string) {
    update(id, { status: "pending", error: undefined, expired: false });
    setAnnouncement("Searching the documents your role can read.");
    try {
      const result = await askQuestion(text);
      if (isDecline(result.answer)) {
        update(id, { status: "declined", answer: result.answer });
        setAnnouncement("Not answered.");
      } else {
        update(id, {
          status: "answered",
          answer: result.answer,
          annotated: annotate(result.answer, result.sources),
        });
        setAnnouncement("Answer ready.");
      }
    } catch (err) {
      const expired = err instanceof ApiError && err.status === 401;
      update(id, {
        status: "error",
        expired,
        error: expired
          ? "Your session has expired. Sign in again to keep asking."
          : "Couldn't reach the server, so this question wasn't answered. Check your connection and try again.",
      });
      setAnnouncement("The question failed.");
    }
  }

  function ask(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;
    const id = nextId++;
    setExchanges((prev) => [...prev, { id, question: trimmed, status: "pending" }]);
    setActiveId(id);
    setQuestion("");
    run(id, trimmed);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    ask(question);
  }

  function focusExchange(id: number) {
    setActiveId(id);
    document.getElementById(`exchange-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // Hover previews; focus and click commit (keyboard users need the panel to
  // stay on the answer they tabbed into). Either way the note is lit wherever
  // it is on screen: the Sources panel when visible, the inline list otherwise.
  function previewNote(id: number, n: number) {
    setPreviewId(id);
    setHighlight({ id, n });
  }

  function endPreview() {
    setPreviewId(null);
    setHighlight(null);
  }

  function commitNote(id: number, n: number) {
    setActiveId(id);
    setHighlight({ id, n });
  }

  function jumpToNote(id: number, n: number) {
    setPreviewId(null);
    commitNote(id, n);
    const panel = document.getElementById(`panel-note-${id}-${n}`);
    const inline = document.getElementById(`note-${id}-${n}`);
    const target = panel && panel.offsetParent !== null ? panel : inline;
    target?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function renderAnswer(ex: Exchange) {
    const notes = ex.annotated?.notes ?? [];
    return (
      <ReactMarkdown
        // GFM for tables, strikethrough and task lists; raw HTML (the model
        // often puts <br> inside table cells) is rendered, then sanitised so
        // nothing executable from model output reaches the page.
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeSanitize]}
        components={{
          table: ({ children }) => (
            <div className={styles.tableWrap}>
              <table>{children}</table>
            </div>
          ),
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noreferrer noopener">
              {children}
            </a>
          ),
          code: ({ children, className }) => {
            const text = String(children);
            if (text.startsWith(FIGURE_MARK)) {
              return <strong className={styles.figure}>{text.slice(FIGURE_MARK.length)}</strong>;
            }
            const group = new RegExp(`^${NOTE_MARK}(\\d+(?:,\\d+)*)$`).exec(text);
            if (!group) return <code className={`${styles.code} ${className ?? ""}`}>{children}</code>;
            // One citation group can name several notes ("§1,2"): each number
            // is its own link to its own note.
            return (
              <sup className={styles.noteRef}>
                {group[1].split(",").map((num) => {
                  const n = Number(num);
                  const note = notes.find((x) => x.n === n);
                  return (
                    <a
                      key={n}
                      href={`#note-${ex.id}-${n}`}
                      style={inkStyle(note?.category)}
                      aria-label={`Source ${n}: ${note?.title ?? "document"}${note?.section ? `, ${note.section}` : ""}`}
                      onMouseEnter={() => previewNote(ex.id, n)}
                      onMouseLeave={endPreview}
                      onFocus={() => commitNote(ex.id, n)}
                      onBlur={() => setHighlight(null)}
                      onClick={(e) => {
                        e.preventDefault();
                        jumpToNote(ex.id, n);
                      }}
                    >
                      {n}
                    </a>
                  );
                })}
              </sup>
            );
          },
        }}
      >
        {ex.annotated?.markdown ?? ex.answer ?? ""}
      </ReactMarkdown>
    );
  }

  return (
    <div className={styles.page}>
      <TopBar>
        <span className={styles.rolePill}>
          <span className={styles.rolePillLabel}>Signed in as</span> {roleLabel(role)}
        </span>
        <button className={styles.signOut} type="button" onClick={signOut} aria-label="Sign out">
          <Icon name="signOut" size={17} />
          <span className={styles.signOutText}>Sign out</span>
        </button>
      </TopBar>

      <div className={styles.body}>
        <AccessRail readable={readable} />

        <div className={styles.main}>
          <div className={styles.thread}>
            <h1 className="sr-only">Ask FinSolve's documents</h1>
            <p className="sr-only" aria-live="polite">
              {announcement}
            </p>

            {exchanges.length === 0 && (
              <EmptyState role={role} readable={readable} onPick={ask} />
            )}

            {exchanges.map((ex) => (
              <article
                key={ex.id}
                id={`exchange-${ex.id}`}
                className={`${styles.exchange} ${ex.id === active?.id ? styles.current : ""}`}
                aria-busy={ex.status === "pending"}
                onClick={() => setActiveId(ex.id)}
              >
                <h2 className={styles.question}>{ex.question}</h2>

                {ex.status === "pending" && (
                  <Searching />
                )}

                {ex.status === "answered" && (
                  <div className={styles.answer}>
                    <div className={styles.prose}>{renderAnswer(ex)}</div>
                    <div className={styles.inlineNotes}>
                      <NoteList
                        exchangeId={ex.id}
                        annotated={ex.annotated}
                        highlight={highlight}
                        idPrefix="note"
                      />
                    </div>
                  </div>
                )}

                {ex.status === "declined" && (
                  <div className={styles.declined}>
                    <p className={styles.calloutTitle}>
                      <Icon name="info" size={18} />
                      Not answered
                    </p>
                    <p>
                      The assistant found nothing it could answer from: either the topic isn't
                      covered by FinSolve's documents, or it sits in a department your role can't
                      read.
                    </p>
                    <p className={styles.nextStep}>
                      Try rephrasing with the terms the documents would use, or ask a colleague in
                      the department that owns this information.
                    </p>
                    <p className={styles.declinedReads}>
                      {roleLabel(role)} can read
                      {readable.map((cat) => (
                        <span key={cat} className={styles.inkTag} style={inkStyle(cat)}>
                          {DEPARTMENTS[cat].label}
                        </span>
                      ))}
                    </p>
                  </div>
                )}

                {ex.status === "error" && (
                  <div className={styles.error} role="alert">
                    <p className={styles.calloutTitle}>
                      <Icon name="alert" size={18} />
                      {ex.expired ? "Session expired" : "Couldn't get an answer"}
                    </p>
                    <p>{ex.error}</p>
                    {ex.expired ? (
                      <button type="button" className={styles.calloutAction} onClick={signOut}>
                        Sign in again
                      </button>
                    ) : (
                      <button
                        type="button"
                        className={styles.calloutAction}
                        onClick={() => run(ex.id, ex.question)}
                      >
                        <Icon name="retry" size={16} />
                        Try again
                      </button>
                    )}
                  </div>
                )}
              </article>
            ))}
            <div ref={threadEndRef} />
          </div>

          <form className={styles.askBar} onSubmit={handleSubmit}>
            <label htmlFor="ask-input" className="sr-only">
              Ask a question about FinSolve's documents
            </label>
            <input
              id="ask-input"
              ref={inputRef}
              className={styles.askInput}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={placeholderFor(readable)}
              autoComplete="off"
              autoFocus
            />
            <button className={styles.askButton} type="submit" disabled={!question.trim()}>
              <Icon name="arrowUp" size={18} />
              Ask
            </button>
          </form>
          <p className={styles.askHint}>
            Each question is answered on its own; the assistant doesn't remember earlier questions.
          </p>
        </div>

        <aside className={styles.notesPanel} aria-label="Sources and session">
          <h2 className={styles.panelTitle}>Sources</h2>
          {shown?.status === "answered" ? (
            <NoteList
              exchangeId={shown.id}
              annotated={shown.annotated}
              highlight={highlight}
              idPrefix="panel-note"
            />
          ) : (
            <p className={styles.panelEmpty}>
              {shown?.status === "pending"
                ? "Sources appear here as soon as the answer arrives."
                : shown?.status === "declined"
                  ? "No sources: this question wasn't answered."
                  : "Ask a question and the documents behind its answer are listed here, numbered to match the answer."}
            </p>
          )}

          {exchanges.length > 1 && (
            <>
              <h2 className={`${styles.panelTitle} ${styles.sessionTitle}`}>This session</h2>
              <ol className={styles.session}>
                {exchanges.map((ex) => (
                  <li key={ex.id}>
                    <button
                      type="button"
                      className={`${styles.sessionItem} ${ex.id === active?.id ? styles.sessionActive : ""}`}
                      aria-current={ex.id === active?.id}
                      onClick={() => focusExchange(ex.id)}
                    >
                      <span className={styles.sessionQuestion}>{ex.question}</span>
                      <span className={`${styles.sessionStatus} ${styles[STATUS_CLASS[ex.status]]}`}>
                        {STATUS_TEXT[ex.status]}
                      </span>
                    </button>
                  </li>
                ))}
              </ol>
            </>
          )}
        </aside>
      </div>
    </div>
  );
}

/** Pending state. Past a few seconds it says why: the API scales to zero when
 *  idle, so the first question after a quiet spell includes a cold start. */
function Searching() {
  const slow = useSlow(true);
  return (
    <div className={styles.searching}>
      <span className={styles.searchBar} aria-hidden="true" />
      <span>
        {slow
          ? "Waking up the assistant. The first question after a quiet spell can take up to a minute…"
          : "Searching the documents your role can read…"}
      </span>
    </div>
  );
}

function placeholderFor(readable: readonly Category[]): string {
  const labels = readable.map((c) => DEPARTMENTS[c].label.toLowerCase());
  if (labels.length === 0) return "Ask a question…";
  if (labels.length >= 4) return "Ask about any department or company policy…";
  return `Ask about ${labels.join(" or ").replace("general", "company policy")}…`;
}

function AccessRail({ readable }: { readable: readonly Category[] }) {
  return (
    <nav className={styles.rail} aria-label="Your access">
      <h2 className={styles.railTitle}>Your access</h2>
      <ul className={styles.deptList}>
        {ALL_CATEGORIES.map((cat) => {
          const can = readable.includes(cat);
          return (
            <li
              key={cat}
              className={`${styles.dept} ${can ? "" : styles.deptOff}`}
              style={inkStyle(cat)}
            >
              <span className={styles.swatch} aria-hidden="true" />
              <span className={styles.deptText}>
                <span className={styles.deptName}>{DEPARTMENTS[cat].label}</span>
                <span className={styles.deptDesc}>{DEPARTMENTS[cat].description}</span>
              </span>
              <span className={styles.deptState}>
                {can ? <Icon name="check" size={16} /> : <Icon name="lock" size={16} />}
                <span className="sr-only">{can ? "can read" : "no access"}</span>
              </span>
            </li>
          );
        })}
      </ul>
      <p className={styles.railNote}>
        Answers only ever come from the departments marked with a tick. The rest are never
        searched for your role.
      </p>
    </nav>
  );
}

function EmptyState({
  role,
  readable,
  onPick,
}: {
  role: string | undefined;
  readable: readonly Category[];
  onPick: (q: string) => void;
}) {
  const examples = role ? (EXAMPLE_QUESTIONS[role] ?? []) : [];
  return (
    <div className={styles.empty}>
      <h2 className={styles.emptyTitle}>What would you like to know?</h2>
      <p className={styles.emptyLede}>
        Answers come only from FinSolve documents in{" "}
        {readable.map((c) => DEPARTMENTS[c].label).join(", ") || "your departments"}, and every
        answer numbers the documents it used.
      </p>
      {examples.length > 0 && (
        <ul className={styles.examples} aria-label="Example questions">
          {examples.map((q) => (
            <li key={q}>
              <button type="button" className={styles.example} onClick={() => onPick(q)}>
                {q}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function NoteList({
  exchangeId,
  annotated,
  highlight,
  idPrefix,
}: {
  exchangeId: number;
  annotated: AnnotatedAnswer | undefined;
  highlight: Highlight | null;
  idPrefix: string;
}) {
  if (!annotated || (annotated.notes.length === 0 && annotated.consulted.length === 0)) {
    return <p className={styles.panelEmpty}>No source documents were returned for this answer.</p>;
  }
  return (
    <div className={styles.noteList}>
      {annotated.notes.length > 0 && (
        <ol className={styles.notes}>
          {annotated.notes.map((note) => (
            <NoteRow
              key={note.n}
              id={`${idPrefix}-${exchangeId}-${note.n}`}
              note={note}
              lit={highlight?.id === exchangeId && highlight.n === note.n}
              marker={<span className={styles.noteNumber}>{note.n}</span>}
            />
          ))}
        </ol>
      )}
      {annotated.consulted.length > 0 && (
        <>
          <p className={styles.consultedLabel}>Also consulted</p>
          <ul className={styles.notes}>
            {annotated.consulted.map((note) => (
              <NoteRow
                key={note.file}
                note={note}
                lit={false}
                marker={<Icon name="document" size={16} className={styles.consultedIcon} />}
              />
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function NoteRow({
  id,
  note,
  lit,
  marker,
}: {
  id?: string;
  note: Note;
  lit: boolean;
  marker: ReactNode;
}) {
  return (
    <li id={id} className={`${styles.note} ${lit ? styles.noteLit : ""}`} style={inkStyle(note.category)}>
      {marker}
      <span className={styles.noteText}>
        <span className={styles.noteTitle}>{note.title}</span>
        {note.section && <span className={styles.noteSection}>{note.section}</span>}
        <span className={styles.noteMeta}>
          {note.category ? `${DEPARTMENTS[note.category].label} · ` : ""}
          {note.file}
        </span>
      </span>
    </li>
  );
}
