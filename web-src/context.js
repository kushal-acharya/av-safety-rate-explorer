import { poisson } from './stats.js';

/** Every category uses the entire selected exposure, never guessed stratum mileage. */
export function contextRows(data, annualRows, dimension, confidence = .95) {
  const categories = data.context_categories[dimension];
  if (!categories) throw new Error('Unknown event context dimension.');
  const keys = new Set(annualRows.map(r => `${r.mode}|${r.manufacturer}|${r.year}`));
  const miles = annualRows.reduce((n,r) => n + r.miles, 0);
  const total = annualRows.reduce((n,r) => n + r.events, 0);
  if (!miles) return [];
  const counts = new Map(categories.map(label => [label, 0]));
  for (const row of data.context[dimension]) {
    if (keys.has(`${row.mode}|${row.manufacturer}|${row.year}`)) {
      if (!counts.has(row.category)) throw new Error('Unrecognized source context label.');
      counts.set(row.category, counts.get(row.category) + row.count);
    }
  }
  if ([...counts.values()].reduce((a,b)=>a+b,0) !== total) throw new Error('Context counts do not reconcile with annual event totals.');
  return categories.map(category => {
    const events = counts.get(category);
    return {category, events, miles, share: total ? events / total : null,
      ...poisson(events, miles, 1-confidence)};
  });
}
