import { useEffect, useState } from "react";

/** How long a request runs before we explain the wait. A warm API answers in a
 *  few seconds; past this, it's almost certainly a cold start (the API scales to
 *  zero when idle and takes up to a minute to load its model). */
export const COLD_START_HINT_MS = 8000;

/** True once `active` has stayed true for `ms`; resets when it goes false. */
export function useSlow(active: boolean, ms = COLD_START_HINT_MS): boolean {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    setSlow(false);
    if (!active) return;
    const timer = window.setTimeout(() => setSlow(true), ms);
    return () => window.clearTimeout(timer);
  }, [active, ms]);
  return slow;
}
