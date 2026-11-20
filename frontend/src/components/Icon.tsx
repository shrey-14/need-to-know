// A small authored icon set: one 24px grid, 1.75 stroke, round caps.
const PATHS = {
  lock: "M7 11V8a5 5 0 0 1 10 0v3M5.5 11h13v9.5h-13z",
  check: "M5 12.5l4.5 4.5L19 7.5",
  info: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5.5M12 7.75v.25",
  arrowUp: "M12 19V5M6 11l6-6 6 6",
  signOut: "M15 4h4v16h-4M10 8l-4 4 4 4M6 12h11",
  document: "M7 3h7l4 4v14H7zM14 3v4h4M9.5 12h6M9.5 15.5h6",
  alert: "M12 8v5M12 16.5v.5M10.3 4.2L2.8 17.5A2 2 0 0 0 4.5 20.5h15a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0z",
  retry: "M4 12a8 8 0 0 1 13.7-5.6L20 9M20 4v5h-5M20 12a8 8 0 0 1-13.7 5.6L4 15M4 20v-5h5",
} as const;

export type IconName = keyof typeof PATHS;

interface IconProps {
  name: IconName;
  size?: number;
  className?: string;
}

export default function Icon({ name, size = 18, className }: IconProps) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
