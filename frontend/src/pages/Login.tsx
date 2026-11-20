import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import TopBar from "../components/TopBar";
import Icon from "../components/Icon";
import { login, ApiError } from "../api/client";
import { saveToken } from "../auth";
import { allowedCategories } from "../roles";
import { DEPARTMENTS, inkStyle, roleLabel } from "../departments";
import styles from "./Login.module.css";

const DEMO_ACCOUNTS = [
  { role: "finance", username: "finance_user", password: "finance123" },
  { role: "marketing", username: "marketing_user", password: "marketing123" },
  { role: "hr", username: "hr_user", password: "hr123" },
  { role: "engineering", username: "engineering_user", password: "engineering123" },
  { role: "employee", username: "employee_user", password: "employee123" },
  { role: "c_level", username: "clevel_user", password: "clevel123" },
];

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pendingRole, setPendingRole] = useState<string | null>(null);
  const [pendingForm, setPendingForm] = useState(false);
  const busy = pendingForm || pendingRole !== null;

  async function authenticate(user: string, pass: string, role?: string) {
    setError(null);
    if (role) setPendingRole(role);
    else setPendingForm(true);
    try {
      const { access_token } = await login(user, pass);
      saveToken(access_token);
      navigate("/chat");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("That username and password don't match. Check them and try again.");
      } else {
        setError("Couldn't reach the server. Check that the backend is running, then try again.");
      }
      setPendingRole(null);
      setPendingForm(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    authenticate(username, password);
  }

  return (
    <div className={styles.page}>
      <TopBar />

      <main className={styles.main}>
        <section className={styles.signIn} aria-labelledby="sign-in-heading">
          <h1 id="sign-in-heading" className={styles.title}>
            Answers from FinSolve's own documents, within your role's access
          </h1>
          <p className={styles.lede}>
            Ask about finance, marketing, HR, engineering or company policy in plain language. Every
            answer lists the documents it came from.
          </p>

          <form onSubmit={handleSubmit} className={styles.form} noValidate>
            <label className={styles.field}>
              <span className={styles.label}>Username</span>
              <input
                className={styles.input}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                autoFocus
              />
            </label>
            <label className={styles.field}>
              <span className={styles.label}>Password</span>
              <input
                className={styles.input}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </label>

            {error && (
              <p className={styles.error} role="alert">
                <Icon name="alert" size={18} />
                {error}
              </p>
            )}

            <button
              className={styles.submit}
              type="submit"
              disabled={busy || !username.trim() || !password}
            >
              {pendingForm ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </section>

        <section className={styles.demo} aria-labelledby="demo-heading">
          <h2 id="demo-heading" className={styles.demoTitle}>
            Or sign in as a demo role
          </h2>
          <p className={styles.demoLede}>
            Each role can read a different set of departments. Try two and ask the same question.
          </p>

          <ul className={styles.roles}>
            {DEMO_ACCOUNTS.map((account) => {
              const cats = allowedCategories(account.role);
              const signingIn = pendingRole === account.role;
              return (
                <li key={account.role}>
                  <button
                    type="button"
                    className={styles.roleButton}
                    disabled={busy}
                    aria-busy={signingIn}
                    onClick={() => authenticate(account.username, account.password, account.role)}
                  >
                    <span className={styles.roleName}>
                      {signingIn ? "Signing in…" : roleLabel(account.role)}
                    </span>
                    <span className={styles.roleReads}>
                      <span className="sr-only">Reads </span>
                      {cats.map((cat) => (
                        <span key={cat} className={styles.inkTag} style={inkStyle(cat)}>
                          {DEPARTMENTS[cat].label}
                        </span>
                      ))}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </section>
      </main>
    </div>
  );
}
