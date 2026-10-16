// Shared one-time fetcher for the static results*.json files in
// public/data/ — every page/panel that needs a report's raw JSON goes
// through here, so the pick-a-strategy screens (mixer, portfolio tracker,
// ranking preview) never refetch a file that's already been loaded this
// session.
const cache = new Map();

export function fetchResults(file) {
  if (!cache.has(file)) {
    const p = fetch(`./data/${file}`)
      .then((r) => {
        if (!r.ok) throw new Error(`Could not load ${file} (${r.status})`);
        return r.json();
      })
      .catch((e) => {
        cache.delete(file);
        throw e;
      });
    cache.set(file, p);
  }
  return cache.get(file);
}
