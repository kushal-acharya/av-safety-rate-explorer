/** @typedef {import('./geography-types').GeographyComparison} GeographyComparison */
/** @typedef {import('./geography-types').SpatialScenario} SpatialScenario */
/** @param {number} value @param {number} [digits] */
const number = (value, digits = 3) =>
  value.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
/** @param {string} value */
const escape = (value) =>
  value.replace(/[&<>"']/g, (character) => `&#${character.charCodeAt(0)};`);
/**
 * Explain the current comparison using the same calculation as the result cards.
 * @param {GeographyComparison} row
 * @param {SpatialScenario} result
 * @param {boolean} observedWeights
 * @returns {string}
 */
export function renderReadingGuide(row, result, observedWeights) {
  return `<details class="geo-reading-guide" id="geo-reading-guide">
    <summary id="geo-guide-summary"><span><strong>Understand these numbers</strong><small>A plain-English walkthrough of your current selection</small></span><span class="guide-chevron" aria-hidden="true">⌄</span></summary>
    <div class="geo-guide-content">
      <p class="geo-guide-context">${escape(row.label)} · ${escape(row.metric_label)}. ${observedWeights ? "Using the source Waymo geographic mileage shares." : "Using your hypothetical comparison settings."} The source period ends in December 2024.</p>
      <ol class="geo-guide-steps">
        <li><h3>Count events, then account for distance.</h3><p>Waymo recorded <b>${row.events} events</b> over <b>${number(row.waymo_miles / 1e6)} million rider-only miles</b>. Divide the events by those miles and multiply by one million.</p><div class="guide-calculation">${row.events} ÷ ${number(row.waymo_miles / 1e6)} = <strong>${number(row.waymo_ipmm)}</strong><span>Waymo events per million miles</span></div></li>
        <li><h3>Choose a human comparison rate.</h3><p>A <b>benchmark</b> is the reference you compare against. With your current settings, it is <b>${number(result.benchmark_ipmm)} events per million miles</b>. This comes from a published human baseline and the chosen geographic weighting and scale.</p><div class="guide-calculation">${number(row.waymo_ipmm)} ÷ ${number(result.benchmark_ipmm)} ≈ <strong>${number(result.ratio, 4)}</strong><span>Rate ratio · Waymo rate / human reference rate</span></div></li>
        <li><h3>Translate that ratio into a percentage.</h3><p>A ratio of 1 means equal rates; below 1 means a lower Waymo rate relative to this reference. Subtract the ratio from 1 and multiply by 100.</p><div class="guide-calculation">(1 − ${number(result.ratio, 4)}) × 100 ≈ <strong>${number(result.reduction_percent, 1)}%</strong><span>Estimated reduction relative to this reference</span></div></li>
      </ol>
      <div class="geo-guide-bottom"><div><h3>What do the sliders change?</h3><p>The mileage slider changes where the human reference puts its weight. The scale slider asks “what if the benchmark were higher or lower?” Neither changes Waymo’s recorded events or miles. Click <b>Reset to source weights</b> to return to the published geographic weighting.</p></div><div><h3>How certain is this number?</h3><p>The displayed interval is <b>${number(result.ratio_lower, 4)}–${number(result.ratio_upper, 4)}</b> for the rate ratio. It includes only uncertainty from Waymo’s event count under the stated Poisson model. The human benchmark and other inputs are treated as fixed; uncertainty about them is not included.</p></div></div>
      <p class="geo-guide-boundary">These are rates over a historical set of miles, not the probability that your next ride will crash. This comparison does not establish that geography caused a safety benefit. Displayed arithmetic uses rounded numbers; the calculation uses full precision.</p>
    </div></details>`;
}
