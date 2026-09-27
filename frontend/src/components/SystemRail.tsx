import type { ReactNode } from "react";
import styles from "./SystemRail.module.css";

interface SystemRailProps {
  title: string;
  children: ReactNode;
}

export default function SystemRail({ title, children }: SystemRailProps) {
  return (
    <aside className={styles.rail}>
      <div className={styles.title}>{title}</div>
      <div className={styles.body}>{children}</div>
    </aside>
  );
}
