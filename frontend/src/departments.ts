// Display metadata for each data category. The category keys mirror
// app/core/roles.py; the inks are the fixed colour language every surface uses
// for that department (access rail, demo-role keys, source notes).
import type { CSSProperties } from "react";
import type { Category } from "./roles";

interface Department {
  label: string;
  description: string;
}

export const DEPARTMENTS: Record<Category, Department> = {
  finance: { label: "Finance", description: "Financial reports and summaries" },
  marketing: { label: "Marketing", description: "Campaign and market reports" },
  hr: { label: "HR", description: "Employee records" },
  engineering: { label: "Engineering", description: "Architecture and processes" },
  general: { label: "General", description: "Handbook and company policy" },
};

export const ROLE_LABELS: Record<string, string> = {
  finance: "Finance",
  marketing: "Marketing",
  hr: "HR",
  engineering: "Engineering",
  employee: "Employee",
  c_level: "C-Level",
};

export function roleLabel(role: string | undefined): string {
  return role ? (ROLE_LABELS[role] ?? role) : "Unknown role";
}

/** CSS custom properties that hand a department's ink to any element. */
export function inkStyle(category: Category | undefined): CSSProperties {
  const key = category ?? "general";
  return {
    "--ink": `var(--ink-${key})`,
    "--ink-soft": `var(--ink-${key}-soft)`,
  } as CSSProperties;
}
