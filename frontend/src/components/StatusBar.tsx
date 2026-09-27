import type { ReactNode } from "react";
import styles from "./StatusBar.module.css";

interface StatusBarProps {
  title: string;
  right?: ReactNode;
}

export default function StatusBar({ title, right }: StatusBarProps) {
  return (
    <div className={styles.bar}>
      <span className={styles.title}>{title}</span>
      {right && <div className={styles.right}>{right}</div>}
    </div>
  );
}
