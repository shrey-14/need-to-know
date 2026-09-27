import styles from "./AnswerTag.module.css";

interface AnswerTagProps {
  variant: "answered" | "declined";
}

export default function AnswerTag({ variant }: AnswerTagProps) {
  const text = variant === "answered" ? "ANSWERED" : "DECLINED";
  return <span className={`${styles.tag} ${styles[variant]}`}>{text}</span>;
}
