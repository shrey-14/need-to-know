import type { ReactNode } from "react";
import styles from "./TerminalPanel.module.css";

interface TerminalPanelProps {
  label?: string;
  children: ReactNode;
  className?: string;
}

export default function TerminalPanel({ label, children, className }: TerminalPanelProps) {
  return (
    <section className={`${styles.panel} ${className ?? ""}`}>
      {label && (
        <div className={styles.labelRow}>
          <span className={styles.label}>{label}</span>
        </div>
      )}
      {children}
    </section>
  );
}
