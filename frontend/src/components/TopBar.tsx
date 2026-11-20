import type { ReactNode } from "react";
import styles from "./TopBar.module.css";

export default function TopBar({ children }: { children?: ReactNode }) {
  return (
    <header className={styles.bar}>
      <div className={styles.wordmark}>
        <span className={styles.company}>FinSolve</span>
        <span className={styles.product}>Assistant</span>
      </div>
      {children && <div className={styles.right}>{children}</div>}
    </header>
  );
}
