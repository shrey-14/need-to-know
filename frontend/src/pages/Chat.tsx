import { useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import StatusBar from "../components/StatusBar";
import AnswerTag from "../components/AnswerTag";
import SystemRail from "../components/SystemRail";
import { askQuestion, ApiError } from "../api/client";
import { getToken, decodeToken, clearToken } from "../auth";
import { ALL_CATEGORIES, allowedCategories } from "../roles";
import { BOOT_LOG } from "../systemStatus";
import { EXAMPLE_QUESTIONS } from "../exampleQuestions";
import styles from "./Chat.module.css";

interface Exchange {
  id: number;
  question: string;
  answer?: string;
  sources?: string[];
  pending: boolean;
  error?: string;
}

function sourceBaseName(path: string): string {
  return path.split("/").pop() ?? path;
}

// The backend has two distinct decline paths with different text — chain.py's own
// short-circuit ("I don't have access to that information.", empty sources) and
// the LLM declining mid-generation ("I don't have that information.", but sources
// still lists whatever context it was given). Sources presence alone can't tell
// these apart from a real answer, so match the actual decline phrasing instead.
function isDecline(answer: string): boolean {
  return answer.toLowerCase().includes("i don't have");
}

// Money, percentages, and standalone figures read as live terminal data —
// direction-contract commitment, not decoration. Wrapped in backticks *before*
// markdown parsing, so they come out the other side as inline-code nodes we
// can re-style as amber figures via the `code` component override below —
// reuses react-markdown's own AST instead of fighting it with string-splitting
// after the fact (which breaks as soon as a figure lands inside **bold** etc).
const FIGURE_PATTERN = /(?:₹|\$)\s?[\d,]+(?:\.\d+)?\s?(?:billion|million|thousand|B|M|K)?|\b\d+(?:\.\d+)?%/g;

function markFigures(text: string): string {
  return text.replace(FIGURE_PATTERN, (match) => `\`${match}\``);
}

let nextId = 1;

export default function Chat() {
  const navigate = useNavigate();
  const token = getToken();
  const role = token ? decodeToken(token)?.role : undefined;
  const accessible = role ? allowedCategories(role) : [];

  const [question, setQuestion] = useState("");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  async function submitQuestion(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;

    const id = nextId++;
    setExchanges((prev) => [...prev, { id, question: trimmed, pending: true }]);
    setQuestion("");
    requestAnimationFrame(() => logEndRef.current?.scrollIntoView({ behavior: "smooth" }));

    try {
      const result = await askQuestion(trimmed);
      setExchanges((prev) =>
        prev.map((ex) =>
          ex.id === id ? { ...ex, pending: false, answer: result.answer, sources: result.sources } : ex,
        ),
      );
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not reach the server.";
      setExchanges((prev) => (prev.map((ex) => (ex.id === id ? { ...ex, pending: false, error: message } : ex))));
    } finally {
      requestAnimationFrame(() => logEndRef.current?.scrollIntoView({ behavior: "smooth" }));
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    submitQuestion(question);
  }

  return (
    <div className={styles.page}>
      <StatusBar
        title={`ROLE: ${role?.toUpperCase() ?? "UNKNOWN"} // SESSION ACTIVE`}
        right={
          <button className={styles.logout} onClick={handleLogout} type="button">
            LOG OUT
          </button>
        }
      />

      <div className={styles.body}>
        <SystemRail title="Access Boundary">
          {ALL_CATEGORIES.map((category) => {
            const lit = accessible.includes(category);
            return (
              <div
                key={category}
                className={`${styles.categoryRow} ${lit ? styles.lit : styles.dim}`}
              >
                <span className={styles.categoryDot} />
                <span>
                  {category.toUpperCase()}
                  {!lit && <span className={styles.categoryNote}> — no access</span>}
                </span>
              </div>
            );
          })}

          <div className={styles.railDivider} />
          <div className={styles.railSubtitle}>System Status</div>
          {BOOT_LOG.map((line) => (
            <div key={line.label} className={styles.bootLine}>
              <span>{line.label}</span>
              <span className={styles.bootStatus}>{line.status}</span>
            </div>
          ))}
        </SystemRail>

        <div className={styles.main}>
          <h1 className={styles.srOnly}>FinSolve Terminal — Chat</h1>
          <main className={styles.log} aria-live="polite">
            {exchanges.length === 0 && (
              <div className={styles.empty}>
                <p className={styles.emptyLead}>
                  Ask a question in plain language. Every answer is grounded in FinSolve's own
                  documents and cited to its source — nothing is invented, and you'll only ever see
                  data your role ({role?.toUpperCase() ?? "UNKNOWN"}) is permitted to access.
                </p>
                {role && EXAMPLE_QUESTIONS[role] && (
                  <>
                    <div className={styles.emptySubtitle}>Try one:</div>
                    <div className={styles.exampleList}>
                      {EXAMPLE_QUESTIONS[role].map((q) => (
                        <button
                          key={q}
                          type="button"
                          className={styles.exampleChip}
                          onClick={() => submitQuestion(q)}
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}

            {exchanges.map((ex) => {
              const isAnswered = !ex.pending && !ex.error && !isDecline(ex.answer ?? "");
              return (
                <div key={ex.id} className={styles.exchange}>
                  <div className={styles.questionLine}>
                    <span className={styles.prompt}>{"›"}</span>
                    <span>{ex.question}</span>
                  </div>

                  {ex.pending && (
                    <div className={styles.computing}>
                      <span className={styles.cursor} />
                      computing…
                    </div>
                  )}

                  {ex.error && (
                    <div className={styles.errorLine} role="alert" aria-live="assertive">
                      {ex.error}
                    </div>
                  )}

                  {!ex.pending && !ex.error && (
                    <div className={isAnswered ? styles.answerBlock : styles.declinedBlock}>
                      <AnswerTag variant={isAnswered ? "answered" : "declined"} />
                      <div className={styles.answerText}>
                        <ReactMarkdown
                          components={{
                            code: ({ children }) => <span className={styles.figure}>{children}</span>,
                          }}
                        >
                          {markFigures(ex.answer ?? "")}
                        </ReactMarkdown>
                      </div>
                      {isAnswered && ex.sources && ex.sources.length > 0 && (
                        <div className={styles.sources}>
                          {ex.sources.map((source) => (
                            <span key={source} className={styles.sourceTag}>
                              [{sourceBaseName(source)}]
                            </span>
                          ))}
                        </div>
                      )}
                      {!isAnswered && (
                        <p className={styles.declinedNote}>
                          This could mean the topic is outside FinSolve's scope, or outside your
                          role's access — see <strong>Access Boundary</strong> in the left rail for
                          what your role can reach.
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
            <div ref={logEndRef} />
          </main>

          <form className={styles.inputBar} onSubmit={handleSubmit}>
            <span className={styles.inputPrompt}>{"›"}</span>
            <input
              className={styles.input}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about finance, marketing, HR, engineering, or company policy…"
              aria-label="Ask a question about FinSolve's data"
              autoFocus
            />
            <button className={styles.send} type="submit" disabled={!question.trim()}>
              SEND
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
