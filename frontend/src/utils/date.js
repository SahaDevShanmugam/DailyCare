/**
 * Parse a datetime string from the API (stored in UTC, often without 'Z' suffix)
 * and return a Date so that .toLocaleString() shows the user's local time.
 */
export function parseServerUtc(dateStr) {
  if (dateStr == null) return new Date(NaN);
  const s = String(dateStr).trim().replace(" ", "T");
  const hasTz = /Z|[+-]\d{2}:?\d{2}$/.test(s);
  const asUtc = hasTz ? s : s.replace(/\.\d+$/, "").replace(/Z$/, "") + "Z";
  return new Date(asUtc);
}

/** Format a server UTC datetime string for display in the user's local timezone. */
export function formatLocalTime(dateStr) {
  const d = parseServerUtc(dateStr);
  return Number.isNaN(d.getTime()) ? String(dateStr) : d.toLocaleString();
}
