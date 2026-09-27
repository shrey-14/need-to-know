// Mirrors app/core/roles.py for display purposes only — this is NOT a security
// boundary. The backend is the only real enforcement point; showing the
// category list here is purely so the UI can dramatize the actual RBAC
// boundary instead of leaving it invisible.
export const ALL_CATEGORIES = ["finance", "marketing", "hr", "engineering", "general"] as const;

export const ROLE_ACCESS: Record<string, readonly string[]> = {
  finance: ["finance", "general"],
  marketing: ["marketing", "general"],
  hr: ["hr", "general"],
  engineering: ["engineering", "general"],
  employee: ["general"],
  c_level: ALL_CATEGORIES,
};

export function allowedCategories(role: string): readonly string[] {
  return ROLE_ACCESS[role] ?? [];
}
