import { renderReadingGuide } from './geography-guide.js';
import { spatialScenario } from './geography.js';
const fmt = (n, d=2) => n.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct = n => `${fmt(n*100,1)}%`;
const cities = [['SAN_FRANCISCO','San Francisco'],['PHOENIX','Phoenix'],['LOS_ANGELES','Los Angeles']];
const metrics = [['airbag','Airbag deployment'],['blincoe_any_injury','Injury · reporting-adjusted'],['observed_any_injury','Injury · police-observed']];
const options = (list, value) => list.map(([id,label])=>`<option value="${id}" ${id===value?'selected':''}>${label}</option>`).join('');
let pending;
function load() {
  if (!pending) pending = fetch('/waymo-project/geography.json').then(r=>{if(!r.ok)throw Error('Could not load the spatial snapshot.');return r.json();}).catch(e=>{pending=null;throw e;});
  return pending;
}
function bandChart(row) {
  const w=620,h=260,l=55,bottom=218,scale=155/Math.max(...row.bands.flatMap(b=>[b.human_share,b.waymo_share]));
  let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Mileage shares across five groups ordered by local human benchmark rate"><title>HPMS and Waymo mileage shares, from lower to higher local benchmark rates</title>`;
  row.bands.forEach((b,i)=>{
    const x=l+i*110;
    svg+=`<rect x="${x}" y="${bottom-b.human_share*scale}" width="30" height="${b.human_share*scale}" rx="3" fill="#9b7851"/><rect x="${x+34}" y="${bottom-b.waymo_share*scale}" width="30" height="${b.waymo_share*scale}" rx="3" fill="#14765e"/><text x="${x+15}" y="${bottom-b.human_share*scale-9}" text-anchor="middle">${pct(b.human_share)}</text><text x="${x+49}" y="${bottom-b.waymo_share*scale-9}" text-anchor="middle">${pct(b.waymo_share)}</text><text x="${x+32}" y="240" text-anchor="middle">${i===0?'Lower':i===4?'Higher':`Band ${i+1}`}</text>`;
  });
  return svg+'</svg>';
}
function curveChart(row, mix, stress) {
  const w=620,h=235,l=55,r=30,t=24,b=43;
  const values=Array.from({length:101},(_,i)=>spatialScenario(row,i/100,stress));
  const min=Math.min(...values.map(v=>v.reduction_lower)),max=Math.max(...values.map(v=>v.reduction_upper));
  const span=max-min||1,lo=min-span*.15,hi=max+span*.15;
  const x=m=>l+m*(w-l-r),y=v=>h-b-(v-lo)/(hi-lo)*(h-t-b);
  let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Estimated rate reduction and conditional 95 percent count interval as geographic weights change"><title>Rate reduction under hypothetical mileage mixtures; shaded interval includes only Waymo count uncertainty</title>`;
  for(let i=0;i<4;i++){const v=lo+(hi-lo)*i/3;svg+=`<line x1="${l}" x2="${w-r}" y1="${y(v)}" y2="${y(v)}" stroke="#dce5d8"/><text x="${l-8}" y="${y(v)+4}" text-anchor="end">${fmt(v,0)}%</text>`;}
  const path=(field,reverse=false)=>(reverse?[...values].reverse():values).map((v,i)=>`${i?'L':'M'}${x(reverse?1-i/100:i/100)},${y(v[field])}`).join(' ');
  svg+=`<path d="${path('reduction_upper')} ${path('reduction_lower',true).replace('M','L')}Z" fill="#dfead9"/><path d="${path('reduction_percent')}" fill="none" stroke="#14765e" stroke-width="3"/>`;
  const current=spatialScenario(row,mix,stress);
  svg+=`<line x1="${x(mix)}" x2="${x(mix)}" y1="${t}" y2="${h-b}" stroke="#31513c" stroke-dasharray="3 4"/><circle cx="${x(mix)}" cy="${y(current.reduction_percent)}" r="6" fill="#14765e" stroke="white" stroke-width="2"/><text x="${l}" y="${h-17}">Human mileage mix</text><text x="${w-r}" y="${h-17}" text-anchor="end">Waymo mileage mix</text></svg>`;
  return svg;
}
function output(study,s) {
  const row=study.comparisons.find(r=>r.city===s.geoCity&&r.metric===s.geoMetric);
  const v=spatialScenario(row,s.geoMix/100,s.geoStress/100),base=spatialScenario(row,0),matched=spatialScenario(row,1);
  const isObserved=s.geoMix===100&&s.geoStress===100;
  const lift=(row.factor-1)*100,pp=matched.reduction_percent-base.reduction_percent;
  return `<div class="geo-results" data-city="${row.city}" data-metric="${row.metric}">
  <article class="geo-verdict"><div class="eyebrow">${isObserved?'OBSERVED GEOGRAPHIC WEIGHTS':'HYPOTHETICAL SENSITIVITY SCENARIO'}</div><div class="geo-big" id="geo-reduction">${fmt(v.reduction_percent,1)}<span>%</span></div><h2>lower observed Waymo rate</h2><p>Relative to this human benchmark, for ${row.metric_label.toLowerCase()} in ${row.label}. An observational comparison, not a causal safety estimate.</p><div class="geo-mini"><div><span>Rate ratio</span><strong id="geo-ratio">${fmt(v.ratio,4)}</strong></div><div><span>Conditional 95% interval</span><strong id="geo-interval">${fmt(v.ratio_lower,4)}–${fmt(v.ratio_upper,4)}</strong></div></div><p class="geo-conditional">Only Waymo count uncertainty is included. The human benchmark, exposure and geographic weights are held fixed. This is not the publisher’s full rate-ratio interval.</p></article>
  <article class="card geo-benchmark"><div class="eyebrow">THE DENOMINATOR CHANGES THE COMPARISON</div><h2>Same events.<br>A different reference.</h2><div class="geo-rate-row"><span>Human · unadjusted</span><strong>${fmt(row.baseline_ipmm,3)}</strong></div><div class="geo-rate-row geo-accent"><span>Human · selected scenario</span><strong id="geo-benchmark">${fmt(v.benchmark_ipmm,3)}</strong></div><div class="geo-rate-row"><span>Waymo · held constant</span><strong>${fmt(row.waymo_ipmm,3)}</strong></div><p class="caption">Events per million miles · ${row.events} Waymo events / ${fmt(row.waymo_miles/1e6,3)} million rider-only miles.</p><div class="geo-insight"><strong>+${fmt(lift,1)}%</strong><p>Human benchmark change from geographic matching alone. The estimated reduction moves from ${fmt(base.reduction_percent,1)}% to ${fmt(matched.reduction_percent,1)}%: <b>+${fmt(pp,1)} percentage points.</b></p></div></article></div>
  ${renderReadingGuide(row,v,isObserved)}
  <div class="geo-chart-grid"><article class="card"><div class="eyebrow">01 / WHERE THE MILES ACCUMULATE</div><h2>The exposure mix</h2><p class="caption">Same geographic cells, different mileage shares.</p><div class="geo-legend"><span><i></i>Human · HPMS</span><span><i></i>Waymo · rider-only</span></div><div class="geo-chart">${bandChart(row)}</div><p class="caption">${row.cells} cells divided into five approximately equal-count bands, ordered by benchmark crashes / HPMS miles. These are not equal-mileage groups or a map of intrinsic road danger. Bars always show the source distributions.</p></article>
  <article class="card"><div class="eyebrow">02 / HOW THE CONCLUSION MOVES</div><h2>Follow the assumption</h2><p class="caption">Estimated rate reduction as mileage weights change.</p><div class="geo-chart">${curveChart(row,s.geoMix/100,s.geoStress/100)}</div><p class="caption">Line: point estimate. Shading: conditional 95% interval from Waymo event counts only. The benchmark scale is fixed at ${s.geoStress}% along this curve. Intermediate mixtures are hypothetical.</p></article></div>
  <section class="study-section" id="geo-audit"><div class="section-heading"><div><h2>Three cities. One reproducible calculation.</h2><p>${row.metric_label} · source period ends December 2024 · not a live feed</p></div><span class="study-match">9 / 9 benchmarks + 9 / 9 counts</span></div><div class="card table-card"><div class="table-scroll" role="region" aria-label="Published and reconstructed geographic benchmarks" tabindex="0"><table id="geo-audit-table"><thead><tr><th scope="col">City</th><th scope="col">Unadjusted</th><th scope="col">Multiplier</th><th scope="col">Reconstructed</th><th scope="col">Published</th><th scope="col">Events</th><th scope="col">Cell coverage</th></tr></thead><tbody>${study.comparisons.filter(r=>r.metric===s.geoMetric).map(r=>`<tr><th scope="row">${r.label}</th><td>${fmt(r.baseline_ipmm,6)}</td><td>${fmt(r.factor,6)}×</td><td>${fmt(r.matched_ipmm,6)}</td><td>${fmt(r.published_matched_ipmm,6)}</td><td>${r.events}</td><td>${fmt(r.coverage*100,3)}%</td></tr>`).join('')}</tbody></table></div><p class="study-table-note">Benchmark agreement checked to absolute tolerance 10⁻⁹ events per million miles before export rounding. Audit values always show the source-weight reconstruction; sliders do not change this table.</p></div></section>
  <div class="geo-coverage"><strong>${fmt(row.coverage*100,3)}% <span>of city miles represented in cells</span></strong><p>${fmt(row.unallocated_miles,0)} of ${fmt(row.waymo_miles,0)} reported miles are outside the summed cell exposure. We normalize geographic weights on the available cells, and use the full city total for the Waymo rate. CSV1 city totals are rounded to 1,000 miles; the gap’s cause is not independently established.</p></div>`;
}
export async function mountGeography(root, settings) {
  root.innerHTML='<div class="empty-state">Loading the frozen geographic evidence…</div>';
  let study;
  try {study=await load();} catch {
    root.innerHTML='<div class="empty-state" role="alert"><h2>Geographic evidence could not load.</h2><p>The other views remain available.</p><button class="small-button" id="geo-retry">Retry</button></div>';
    root.querySelector('#geo-retry').onclick=()=>mountGeography(root,settings);return;
  }
  const s={...settings};
  root.innerHTML=`<div class="study-masthead geo-masthead"><div class="eyebrow">RESEARCH NOTE 002 <span class="study-separator">/</span> GEOGRAPHIC EXPOSURE MATCHING</div><h1>Same miles.<br><em>Different benchmark.</em></h1><p>Where a vehicle drives changes the comparison. Reconstruct the human benchmark on Waymo’s geographic mileage mix, then test how much the result depends on that choice.</p><div class="study-meta"><span>3 cities</span><span>987 geographic cells</span><span>2022 human benchmark</span><span>Waymo through Dec 2024</span></div><div class="study-seal"><strong>9<span> / 9</span></strong><span>benchmarks reproduced</span><small>Source classifications and human baseline supplied by Waymo</small></div></div>
  <div class="study-jump"><a href="#geo-controls">Explore the adjustment ↓</a><a href="#geo-audit">Inspect the audit ↓</a><a href="#geo-method">Reproduce the method ↓</a></div>
  <div class="study-controls" id="geo-controls"><div><label for="geo-city">OPERATING CITY</label><select id="geo-city">${options(cities,s.geoCity)}</select></div><div><label for="geo-metric">COLLISION OUTCOME</label><select id="geo-metric">${options(metrics,s.geoMetric)}</select></div><button id="geo-reset" class="small-button">Reset to source weights ↺</button></div>
  <div class="geo-sliders"><div><label for="geo-mix">Geographic mileage mix <output id="geo-mix-value">${s.geoMix}% toward Waymo</output></label><input id="geo-mix" type="range" min="0" max="100" step="1" value="${s.geoMix}" aria-describedby="geo-mix-help"><div class="geo-range-labels"><span>Human mileage shares</span><span>Waymo mileage shares</span></div><p id="geo-mix-help">Interpolate the two observed distributions. Values between endpoints are hypothetical.</p></div><div><label for="geo-stress">Benchmark scale <output id="geo-stress-value">${s.geoStress}% of source</output></label><input id="geo-stress" type="range" min="50" max="150" step="1" value="${s.geoStress}" aria-describedby="geo-stress-help"><div class="geo-range-labels"><span>50%</span><span>100% · source</span><span>150%</span></div><p id="geo-stress-help">A hypothetical stress test, not a measured uncertainty range or confidence level.</p></div></div>
  <div id="geo-output"></div>
  <section class="study-section" id="geo-method"><div class="section-heading"><div><h2>From source cells to a matched reference.</h2><p>Reconstruct the adjustment. Preserve the dependencies.</p></div></div><div class="study-source-grid"><article class="card"><div class="eyebrow">THE REWEIGHTING</div><h3>Compare the same geographic support.</h3><p>For each cell, divide allocated human benchmark crashes C by HPMS vehicle miles H. Average those cell rates with Waymo mileage W as weights, then divide by the human-mileage-weighted average.</p><div class="study-command">factor = [Σ(W × C/H) / ΣW] / [ΣC / ΣH]<br>matched benchmark = published baseline × factor<br>scenario = baseline × [1 + mix × (factor − 1)] × scale</div><p>The relative factor calibrates the published passenger-vehicle baseline. Raw HPMS mileage includes other vehicle types; its uncalibrated rate is not used as an absolute passenger benchmark. Reporting-adjusted injury rates already include the publisher’s adjustment.</p><div class="source-links"><a href="https://arxiv.org/abs/2410.08903" target="_blank" rel="noopener">Chen et al. · method, v1 ↗</a><a href="/waymo-project/geography-manifest.json" download>Source URLs & SHA-256 hashes ↓</a></div></article><article class="card"><div class="eyebrow">THE REPRODUCTION</div><h3>Four frozen files. An inspectable audit.</h3><p>March 19, 2025 release: rider-only miles, event classifications, published comparisons and geographic cells. Re-extract all four sources with hash verification, reconstruct nine benchmarks and recount nine event cohorts.</p><pre class="study-command">uv run python scripts/reproduce_geography.py \\
  --from-source --check</pre><div class="source-links">${[['cells','987 cells × 3 outcomes'],['events','523 source event rows'],['inputs','9 reference inputs'],['results','Reproduction audit']].map(([file,label])=>`<a href="/waymo-project/geography-${file}.csv" download>${label} ↓</a>`).join('')}<a href="https://github.com/kushal-acharya/av-safety-rate-explorer/blob/main/docs/geographic-exposure.md" target="_blank" rel="noopener">Technical note ↗</a></div><p>Source row numbers preserve two missing SGO identifiers and an identifier repeated across cities. We retain source membership rather than deduplicating by report ID. Austin is excluded from spatial comparisons because this release provides no Austin cells.</p></article></div><div class="study-limits"><h3>What this experiment establishes—and what it leaves open</h3><p>This reproduces the publisher’s spatial adjustment using its allocated benchmark counts, mileage, baseline rates and event classifications. It does not independently reconstruct raw human crash data or adjudicate events. Geographic matching does not control time of day, weather, road conditions, vehicle mix or reporting differences, and does not establish causality.</p><p>The displayed intervals include only Poisson uncertainty in Waymo counts. Human benchmark uncertainty, geographic weights, reporting adjustment and mileage error are excluded. No claim is made to reproduce the publisher’s full confidence intervals. This snapshot is separate from the 2023 publication-reproduction study and the DMV disengagement dataset.</p></div></section>`;
  const refresh=()=>{
    root.querySelector('#geo-mix-value').textContent=`${s.geoMix}% toward Waymo`;
    root.querySelector('#geo-stress-value').textContent=`${s.geoStress}% of source`;
    const guideOpen = root.querySelector('#geo-reading-guide')?.open || false;
    root.querySelector('#geo-output').innerHTML=output(study,s);
    root.querySelector('#geo-reading-guide').open=guideOpen;
    root.querySelector('#geo-mix').setAttribute('aria-valuetext',`${s.geoMix}% toward Waymo mileage distribution`);
    root.querySelector('#geo-stress').setAttribute('aria-valuetext',`${s.geoStress}% of source benchmark`);
  };
  for(const [id,key,numeric] of [['geo-city','geoCity',false],['geo-metric','geoMetric',false],['geo-mix','geoMix',true],['geo-stress','geoStress',true]]) {
    root.querySelector(`#${id}`).addEventListener(numeric?'input':'change',e=>{s[key]=numeric?Number(e.target.value):e.target.value;refresh();settings.onChange({[key]:s[key]});});
  }
  root.querySelector('#geo-reset').onclick=()=>{s.geoMix=100;s.geoStress=100;root.querySelector('#geo-mix').value=100;root.querySelector('#geo-stress').value=100;refresh();settings.onChange({geoMix:100,geoStress:100});};
  refresh();
  if(location.hash === '#geo-reading-guide') {
    root.querySelector('#geo-reading-guide').open=true;
    requestAnimationFrame(()=>{
      root.querySelector('#geo-reading-guide').scrollIntoView({block:'start'});
      root.querySelector('#geo-guide-summary').focus({preventScroll:true});
    });
  }
}
