export async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  const data = await res.json();
  if (!res.ok || data.ok === false) {
    const message = data?.error?.message || `Request failed (${res.status})`;
    const error = new Error(message);
    error.details = data?.error?.details || data;
    throw error;
  }
  return data;
}
