/**
 * Utility to extract readable error messages from API responses.
 * FastAPI validation errors return { detail: [{ msg: "...", loc: [...] }] },
 * which stringifies to "[object Object]" if not parsed properly.
 */
export function parseApiError(detail, fallback = 'An unexpected error occurred') {
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item?.msg) {
          const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : null;
          return field && field !== 'body' ? `${field}: ${item.msg}` : item.msg;
        }
        return JSON.stringify(item);
      })
      .join(', ');
  }

  if (typeof detail === 'object') {
    return detail.message || detail.msg || JSON.stringify(detail);
  }

  return String(detail);
}
