import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import StatusBar from "../components/StatusBar";
import TerminalPanel from "../components/TerminalPanel";
import SystemRail from "../components/SystemRail";
import { login, ApiError } from "../api/client";
import { saveToken } from "../auth";
import { BOOT_LOG } from "../systemStatus";
import { ALL_CATEGORIES } from "../roles";
import styles from "./Login.module.css";

const DEMO_ACCOUNTS = [
  { key: "F1", label: "FINANCE", username: "finance_user", password: "finance123" },
  { key: "F2", label: "MARKETING", username: "marketing_user", password: "marketing123" },
  { key: "F3", label: "HR", username: "hr_user", password: "hr123" },
  { key: "F4", label: "ENGINEERING", username: "engineering_user", password: "engineering123" },
  { key: "F5", label: "EMPLOYEE", username: "employee_user", password: "employee123" },
  { key: "F6", label: "C_LEVEL", username: "clevel_user", password: "clevel123" },
];

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [pressedKey, setPressedKey] = useState<string | null>(null);

  async function authenticate(user: string, pass: string, key?: string) {
    setError(null);
    setPending(true);
    setPressedKey(key ?? null);
    try {
      const { access_token } = await login(user, pass);
      saveToken(access_token);
      navigate("/chat");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the server.");
      setPressedKey(null);
    } finally {
      setPending(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    authenticate(username, password);
  }

  return (
    <div className={styles.page}>
      <StatusBar title="FINSOLVE TERMINAL — SECURE ACCESS" />

      <div className={styles.body}>
        <SystemRail title="System Status">
          {BOOT_LOG.map((line) => (
            <div key={line.label} className={styles.bootLine}>
              <span>{line.label}</span>
              <span className={styles.bootStatus}>{line.status}</span>
            </div>
          ))}

          <div className={styles.railDivider} />
          <div className={styles.railSubtitle}>Data Categories</div>
          {ALL_CATEGORIES.map((category) => (
            <div key={category} className={styles.categoryLine}>
              <span className={styles.categoryDot} />
              <span>{category.toUpperCase()}</span>
            </div>
          ))}
        </SystemRail>

        <main className={styles.content}>
          <p className={styles.valueProp}>
            Ask questions about FinSolve's finance, marketing, HR, engineering, and policy data in
            plain language — every answer is cited to its source and scoped to your role.
          </p>
          <TerminalPanel label="FINSOLVE — Secure Access Terminal" className={styles.console}>
            <div className={styles.consoleGrid}>
              <div className={styles.consoleRegion}>
                <div className={styles.regionTitle}>Authenticate</div>
                <form onSubmit={handleSubmit} className={styles.form}>
                  <label className={styles.field}>
                    <span className={styles.fieldLabel} id="user-label">USER:</span>
                    <input
                      className={styles.input}
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      autoComplete="username"
                      aria-labelledby="user-label"
                      autoFocus
                    />
                  </label>
                  <label className={styles.field}>
                    <span className={styles.fieldLabel} id="pass-label">PASS:</span>
                    <input
                      className={styles.input}
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      autoComplete="current-password"
                      aria-labelledby="pass-label"
                    />
                  </label>

                  {error && (
                    <p className={styles.error} role="alert" aria-live="assertive">
                      {error}
                    </p>
                  )}

                  <button className={styles.submit} type="submit" disabled={pending}>
                    {pending && !pressedKey ? "AUTHENTICATING…" : "ENTER TERMINAL"}
                  </button>
                </form>
              </div>

              <div className={styles.consoleDivider} />

              <div className={styles.consoleRegion}>
                <div className={styles.regionTitle}>Demo accounts — one-click access</div>
                <div className={styles.demoGrid}>
                  {DEMO_ACCOUNTS.map((account) => (
                    <button
                      key={account.key}
                      type="button"
                      className={`${styles.demoKey} ${pressedKey === account.key ? styles.demoKeyActive : ""}`}
                      disabled={pending}
                      aria-pressed={pressedKey === account.key}
                      onClick={() => authenticate(account.username, account.password, account.key)}
                    >
                      <span className={styles.demoKeyId}>{account.key}</span>
                      <span>{pressedKey === account.key ? "SIGNING IN…" : account.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </TerminalPanel>
        </main>
      </div>
    </div>
  );
}
