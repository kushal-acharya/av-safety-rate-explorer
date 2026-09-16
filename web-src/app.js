import { poisson, zeroBound, ratio, plan, powerAt, interval } from './stats.js';

const $ = id => document.getElementById(id);
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (n, digits = 2) => Number.isFinite(n) ? n.toLocaleString('en-US', { maximumFractionDigits: digits }) : '—';
const compact = n => n >= 1e9 ? `${fmt(n / 1e9, 2)}B` : n >= 1e6 ? `${fmt(n / 1e6, 2)}M` : n >= 1e4 ? `${fmt(n / 1e3, 1)}k` : fmt(n, 1);
const rateFmt = n => n === 0 ? '0' : n < .001 ? n.toExponential(2) : fmt(n, n < .1 ? 4 : 3);
const options = (values, selected) => values.map(([v, label]) => `<option value="${esc(v)}" ${String(v) === String(selected) ? 'selected' : ''}>${esc(label)}</option>`).join('');
let data;
const state = { tab: 'rates', companies: ['Waymo'], years: [2020,2021,2022,2023,2024], mode: 'safety-driver', confidence: .95, unit: 1000, method: 'auto' };
let plannerInitialized = false, compareA = '', compareB = '';
const planner = { baseline: .08, reduction: 10, alpha: .05, power: .8, phi: 1, allocation: .5, twoSided: true };
const params = new URLSearchParams(location.search);
for (const k of ['tab','mode','method']) if (params.has(k)) state[k] = params.get(k);
if (params.has('companies')) state.companies = params.get('companies').split(',');
if (params.has('years')) state.years = params.get('years').split(',').map(Number).filter(y=>y>=2020&&y<=2024);
if ([.9,.95,.99].includes(Number(params.get('confidence')))) state.confidence = Number(params.get('confidence'));
if ([1000,100000].includes(Number(params.get('unit')))) state.unit = Number(params.get('unit'));
if (!['rates','compare','planner','methods'].includes(state.tab)) state.tab = 'rates';
if (!['safety-driver','driverless'].includes(state.mode)) state.mode = 'safety-driver';
if (!['auto','poisson','nb'].includes(state.method)) state.method = 'auto';
const conf = () => `${Math.round(state.confidence * 100)}%`;
const unitLabel = () => `per ${fmt(state.unit, 0)} miles`;
const selectedRows = () => data.annual.filter(r => r.mode === state.mode && state.years.includes(r.year) && state.companies.includes(r.manufacturer) && r.eligible);
const sum = (rows, field) => rows.reduce((a,r)=>a+r[field],0);
function fitFor(name, years) {
  const available = data.annual.filter(r => r.manufacturer === name && r.mode === state.mode && years.includes(r.year)).map(r=>r.year).sort();
  return data.fits[`${state.mode}|${name}|${available.join(',')}`];
}
function groups() {
  const rows = selectedRows();
  if (state.companies.length === 1) return rows.map(r=>({...r, label:String(r.year), ...interval(r, fitFor(r.manufacturer,[r.year]),state.method,1-state.confidence)}));
  return [...new Set(rows.map(r=>r.manufacturer))].sort().map(name=>{
    const group = rows.filter(r=>r.manufacturer===name), r={ label:name, manufacturer:name, events:sum(group,'events'), miles:sum(group,'miles') };
    return {...r,...interval(r,fitFor(name,state.years),state.method,1-state.confidence)};
  });
}
function updateURL() {
  const query = new URLSearchParams();
  Object.entries(state).forEach(([key,value])=>query.set(key,Array.isArray(value)?value.join(','):value));
  history.replaceState(null,'',`${location.pathname}?${query}`);
}
function toast(message) { $('toast').textContent=message; $('toast').classList.add('visible'); setTimeout(()=>$('toast').classList.remove('visible'),3000); }
function setTab(tab) { state.tab=tab; render(); }
function heading(index,title,subtitle,badge='') {
  return `<div class="section-heading"><div><h2><span class="section-index">${index}</span>${title}</h2><p>${subtitle}</p></div>${badge?`<span class="pill"><span class="status-dot"></span>${badge}</span>`:''}</div>`;
}
function empty() { return `<div class="empty-state"><h3>No exposure in this selection.</h3><p>Choose a manufacturer and reporting year with recorded miles.<br>Driverless reports are available for 2023–2024 only.</p><button class="primary-button" data-reset>Reset filters</button></div>`; }
function refreshFilters() {
  $('company-summary').innerHTML=`${state.companies.length===1?esc(state.companies[0]):state.companies.length?`${state.companies.length} selected`:'None selected'} <span>⌄</span>`;
  $('company-options').innerHTML=[...new Set(data.annual.map(r=>r.manufacturer))].sort().map(name=>`<label><input type="checkbox" value="${esc(name)}" ${state.companies.includes(name)?'checked':''}>${esc(name)}</label>`).join('');
  $('year-buttons').innerHTML=data.years.map(y=>`<button class="${state.years.includes(y)?'selected':''}" aria-pressed="${state.years.includes(y)}" data-year="${y}" ${state.mode==='driverless'&&y<2023?'disabled':''}>${y}</button>`).join('');
  $('mode').value=state.mode; $('confidence').value=String(state.confidence);
}
function plotRates(rows) {
  const w=window.innerWidth<=760&&state.companies.length===1?390:660,h=Math.max(255,rows.length*43+65),l=state.companies.length===1?54:132,r=88,t=28,b=40;
  const max=Math.max(...rows.map(d=>d.upper*state.unit))*1.1 || 1;
  const log=state.companies.length>1;
  const positive=rows.flatMap(d=>[d.lower,d.rate,d.upper]).filter(v=>v>0).map(v=>v*state.unit);
  const min=log?Math.min(...positive)/1.5:0;
  const x=v=>l+(log?(Math.log10(Math.max(min,v))-Math.log10(min))/(Math.log10(max)-Math.log10(min)):v/max)*(w-l-r);
  const y=i=>t+(i+.5)*(h-t-b)/rows.length;
  let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Disengagement rates with ${conf()} confidence intervals"><title>Disengagement rates ${unitLabel()}, ${conf()} confidence intervals</title>`;
  for(let i=0;i<5;i++) { const value=log?10**(Math.log10(min)+(Math.log10(max)-Math.log10(min))*i/4):max*i/4,xx=x(value); svg+=`<line x1="${xx}" x2="${xx}" y1="${t-10}" y2="${h-b+3}" stroke="#edf1e7"/><text x="${xx}" y="${h-17}" text-anchor="middle" fill="#596b5d" font-size="9">${rateFmt(value)}</text>`; }
  rows.forEach((d,i)=>{ const yy=y(i),lo=x(d.lower*state.unit),hi=x(d.upper*state.unit),xx=x((d.events?d.rate:d.upper)*state.unit);svg+=`<text x="${l-16}" y="${yy+3}" text-anchor="end" font-size="11" fill="#61765f">${esc(d.label)}</text><line x1="${lo}" x2="${hi}" y1="${yy}" y2="${yy}" stroke="#8eb6a0" stroke-width="3"/><line x1="${lo}" x2="${lo}" y1="${yy-6}" y2="${yy+6}" stroke="#8eb6a0"/><line x1="${hi}" x2="${hi}" y1="${yy-6}" y2="${yy+6}" stroke="#8eb6a0"/><circle tabindex="0" class="tooltip-point" cx="${xx}" cy="${yy}" r="5" fill="${d.events?'#087d68':'#c77a50'}" stroke="white" stroke-width="2"><title>${esc(d.label)}: ${d.events?rateFmt(d.rate*state.unit):'zero events; upper bound'} ${unitLabel()}; ${conf()} CI [${rateFmt(d.lower*state.unit)}, ${rateFmt(d.upper*state.unit)}]; ${d.method}</title></circle><text x="${w-r+17}" y="${yy+4}" font-size="11" fill="#3b6752">${d.events?rateFmt(d.rate*state.unit):'&lt; '+rateFmt(d.upper*state.unit)}</text>`; });
  svg+=`<text x="${(w+l-r)/2}" y="${h-1}" text-anchor="middle" font-size="8" fill="#596b5d">DISENGAGEMENTS ${unitLabel().toUpperCase()}${log?' · LOG SCALE':''}</text></svg>`;
  return svg;
}
function renderRates() {
  const rows=selectedRows(),g=groups();
  if(!rows.length){$('view-rates').innerHTML=heading('01','Rate explorer','Follow the rate. Keep the uncertainty in view.')+empty();return;}
  const miles=sum(rows,'miles'),events=sum(rows,'events'),p=poisson(events,miles,1-state.confidence);
  const companies=[...new Set(rows.map(r=>r.manufacturer))].length;
  const warnings=[...new Set(g.map(r=>r.warning).filter(Boolean))];
  const nb=g.filter(r=>r.method.startsWith('NB')).length;
  $('view-rates').innerHTML=heading('01','Rate explorer','Follow the rate. Keep the uncertainty in view.',`${rows.length} reporting groups`)+`
    <div class="metric-grid"><div class="metric"><div class="metric-label">Autonomous exposure <span>↗</span></div><div class="metric-value">${compact(miles)}<small>miles</small></div><div class="metric-foot">${companies} ${companies===1?'manufacturer':'manufacturers'} · ${state.mode==='driverless'?'driverless testing':'safety-driver testing'}</div></div>
    <div class="metric"><div class="metric-label">Reported disengagements <span>◎</span></div><div class="metric-value">${fmt(events,0)}<small>events</small></div><div class="metric-foot">Reconciled with event-level reports</div></div>
    <div class="metric featured"><div class="metric-label">Observed pooled rate <span>⌁</span></div><div class="metric-value">${events?rateFmt(p.rate*state.unit):'&lt; '+rateFmt(p.upper*state.unit)}<small>${unitLabel()}</small></div><div class="metric-foot">${conf()} exact CI: ${rateFmt(p.lower*state.unit)}–${rateFmt(p.upper*state.unit)}${events?'':' · upper bound only'}</div></div></div>
    <div class="content-grid"><article class="card"><div class="card-title"><div><h3>${state.companies.length===1?`${esc(state.companies[0])}, across the years`:'Rates, with room for uncertainty'}</h3><p class="card-subtitle">${conf()} intervals · ${nb?`${nb} NB fit${nb>1?'s':''}, ${g.length-nb} exact Poisson`:'Exact Poisson intervals'}</p></div><span class="mini-badge">${conf()} CI</span></div>
    <div class="chart-controls"><label for="interval-method">Interval</label><select id="interval-method">${options([['auto','Auto · dispersion check'],['poisson','Poisson exact'],['nb','Negative binomial']],state.method)}</select><label for="rate-unit">Scale</label><select id="rate-unit">${options([[1000,'Per 1,000 miles'],[100000,'Per 100,000 miles']],state.unit)}</select></div>
    <div class="chart-frame">${plotRates(g)}</div><div class="chart-legend"><span><i class="legend-point"></i>Estimated rate</span><span><i class="legend-line"></i>${conf()} confidence interval</span><span style="color:#96603c">● Zero-event upper bound</span></div>
    <p class="caption">Exposure is the denominator. Auto selects NB when the VIN-year Pearson diagnostic suggests overdispersion and the fit is identifiable. NB estimates can differ from the observed pooled rate.</p>${warnings.length?`<div class="warning">${warnings.map(esc).join('<br>')}</div>`:''}</article>
    <article class="card insight-card"><div><div class="insight-icon">◎</div><span class="insight-kicker">THE ZERO-EVENT PARADOX</span><h3>Zero events.<br>Not zero risk.</h3><p>Even a spotless test run leaves uncertainty. More miles narrow the upper bound.</p></div><div class="insight-example"><label for="zero-miles">Try a hypothetical zero-event run</label><input id="zero-miles" type="range" min="3" max="7" step=".1" value="5" aria-label="Log scale miles for hypothetical zero-event run"><small id="zero-exposure"></small><strong id="zero-value"></strong><small>${unitLabel()} · ${conf()} one-sided upper bound</small><p class="caption">−ln(1 − confidence) ÷ miles.<br>At 95%, this is the rule of three.<br>The two-sided 95% bound uses 3.689.</p></div></article></div>
    <article class="card data-card"><div class="card-title"><div><h3>The evidence behind the estimate</h3><p class="card-subtitle">Every count, denominator, and interval in one place.</p></div><div class="table-controls"><button id="export-csv">↓ Export CSV</button></div></div><div class="table-wrap"><table><thead><tr><th>${state.companies.length===1?'YEAR':'MANUFACTURER'}</th><th class="num">MILES</th><th class="num">EVENTS</th><th class="num">RATE / ${fmt(state.unit,0)} MI</th><th class="num">${conf()} CI</th><th>METHOD</th></tr></thead><tbody>${g.map(d=>`<tr><td>${esc(d.label)}</td><td class="num">${fmt(d.miles,1)}</td><td class="num">${fmt(d.events,0)}</td><td class="num">${d.events?rateFmt(d.rate*state.unit):'Upper bound only'}</td><td class="num">${rateFmt(d.lower*state.unit)}–${rateFmt(d.upper*state.unit)}</td><td><span class="method-label">${esc(d.method)}</span></td></tr>`).join('')}</tbody></table></div><p class="caption">${state.companies.length>1?'Manufacturer comparisons reflect different operating domains, intervention thresholds, and testing strategies. They are not safety rankings.':'Reporting years run December–November. Changes across years are observational, not randomized release comparisons.'}</p></article>
    <div class="bottom-strip"><div><h3>How many miles would it take to detect a real change?</h3><p>Turn this observed rate into an experiment design.</p></div><button class="primary-button" id="use-baseline">Open the planner ↗</button></div>`;
  $('interval-method').onchange=e=>{state.method=e.target.value;render();};
  $('rate-unit').onchange=e=>{state.unit=Number(e.target.value);render();};
  const updateZero=()=>{const m=10**Number($('zero-miles').value);$('zero-exposure').textContent=`0 events in ${compact(m)} miles`;$('zero-value').textContent=`< ${rateFmt(zeroBound(m,state.confidence)*state.unit)}`;};
  $('zero-miles').oninput=updateZero;updateZero();
  $('export-csv').onclick=exportCSV;
  $('use-baseline').onclick=()=>{setPlannerBaseline();setTab('planner');};
}
function exportCSV() {
  const fields=['label','miles','events','rate','lower','upper','method'];
  const csv=[fields.concat(['rate_units','confidence']).join(','),...groups().map(r=>fields.map(k=>JSON.stringify(r[k])).concat(['"events per mile"',state.confidence]).join(','))].join('\n');
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv'})),a=document.createElement('a');a.href=url;a.download='av-evidence-selection.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Selection exported with units and confidence level.');
}
function renderCompare() {
  const rows=selectedRows();
  if(rows.length<2){$('view-compare').innerHTML=heading('02','Compare groups','Two reporting groups. One transparent comparison.')+`<div class="empty-state"><h3>Choose at least two reporting groups.</h3><p>Select two years for one manufacturer, or multiple manufacturers above.</p></div>`;return;}
  const key=r=>`${r.manufacturer}|${r.year}`;
  if(!rows.some(r=>key(r)===compareA))compareA=key(rows[0]);
  if(!rows.some(r=>key(r)===compareB)||compareB===compareA)compareB=key(rows.find(r=>key(r)!==compareA));
  const a=rows.find(r=>key(r)===compareA),b=rows.find(r=>key(r)===compareB),rr=ratio(a.events,a.miles,b.events,b.miles,1-state.confidence);
  const chooser=(r,side)=>{const p=poisson(r.events,r.miles,1-state.confidence);return `<article class="group-card"><label for="group-${side}">GROUP ${side.toUpperCase()} · ${side==='a'?'REFERENCE':'COMPARISON'}</label><select id="group-${side}">${options(rows.map(x=>[key(x),`${x.manufacturer} · ${x.year}`]),key(r))}</select><div class="metric-value">${r.events?rateFmt(p.rate*state.unit):'&lt; '+rateFmt(p.upper*state.unit)}<small>${unitLabel()}</small></div><p class="caption">${conf()} exact CI: ${rateFmt(p.lower*state.unit)}–${rateFmt(p.upper*state.unit)}<br>${fmt(r.events,0)} events / ${fmt(r.miles,1)} miles</p></article>`;};
  const change=rr.ratio===null?'The ratio is not finite.':rr.ratio===0?'No events were reported in group B.':`B’s observed rate is ${fmt(Math.abs(rr.ratio-1)*100,1)}% ${rr.ratio<1?'lower':'higher'}.`;
  const excludes=rr.upper!==null&&(rr.upper<1||rr.lower>1);
  $('view-compare').innerHTML=heading('02','Compare groups','Two reporting groups. One transparent comparison.','B ÷ A')+`<div class="compare-selects">${chooser(a,'a')}<div class="vs">VS</div>${chooser(b,'b')}</div><article class="comparison-outcome"><div><span class="eyebrow">OBSERVED DIFFERENCE</span><h3>${change}</h3><p>${rr.ratio===null?'A finite rate ratio cannot be estimated when the reference group has zero events.':`The ${conf()} interval ${excludes?'excludes':'includes'} 1 (equal rates).`} This is a comparison of reported disengagements under different conditions, not a causal claim about safety.</p></div><div><div class="metric-label">Rate ratio · B / A</div><div class="ratio-stat">${rr.ratio===null?'Not estimable':fmt(rr.ratio,3)}<small style="font-size:13px"> ${rr.ratio===null?'':'×'}</small></div><p>${conf()} CI: ${fmt(rr.lower,3)}–${rr.upper===null?'∞':fmt(rr.upper,3)}<br>Exact conditional p-value: ${rr.p<.0001?'< 0.0001':fmt(rr.p,4)}</p></div></article><div class="card"><h3>Read the comparison carefully</h3><p class="caption">${esc(rr.method)}. Both group rates use exact Poisson intervals, independent of the Rate explorer’s interval setting. Poisson inference assumes independent events and constant rates; overdispersion can make it too optimistic. No adjustment for multiple comparisons, geography, weather, fleet mix, or reporting practices.</p><div class="warning">A reporting year is not a software release. These observational data cannot establish that one release or company is safer.</div></div>`;
  $('group-a').onchange=e=>{compareA=e.target.value;if(compareA===compareB)compareB='';renderCompare();};
  $('group-b').onchange=e=>{compareB=e.target.value;if(compareA===compareB)compareA=key(rows.find(r=>key(r)!==compareB));renderCompare();};
}
function setPlannerBaseline() {
  const rows=selectedRows(),m=sum(rows,'miles'),k=sum(rows,'events');
  if(m&&k)planner.baseline=k/m*1000;
  planner.phi=1;
  if(state.companies.length===1){const fit=fitFor(state.companies[0],state.years);if(fit&&Number.isFinite(fit.phi))planner.phi=Math.max(1,fit.phi);}
  plannerInitialized=true;
}
function renderPlanner() {
  if(!plannerInitialized)setPlannerBaseline();
  const rows=selectedRows(),noBaseline=!rows.length||sum(rows,'events')===0;
  $('view-planner').innerHTML=heading('03','Plan the next million miles','Find the exposure needed to detect a meaningful reduction.','Normal approximation')+`<div class="planner-grid"><article class="card"><h3>Design your experiment</h3><p class="card-subtitle">Two independent arms · constant event rates</p>
  <div class="input-group"><label for="baseline">Baseline rate / 1,000 miles</label><input id="baseline" type="number" min="0.000001" max="100000" step="any" value="${planner.baseline}"><small>${noBaseline?'No positive observed rate in this selection; enter a planning assumption.':'Initially uses the selection’s observed pooled rate.'}</small></div>
  <div class="input-group"><label for="reduction">Target reduction <output id="reduction-value">${planner.reduction}%</output></label><input id="reduction" type="range" min="1" max="80" value="${planner.reduction}"><small>A relative reduction in the event rate</small></div>
  <div class="input-group"><label for="power">Statistical power</label><select id="power">${options([[.8,'80% power'],[.9,'90% power'],[.95,'95% power']],planner.power)}</select></div>
  <div class="input-group"><label for="alpha">Significance level · α</label><select id="alpha">${options([[.1,'10%'],[.05,'5%'],[.01,'1%']],planner.alpha)}</select></div>
  <div class="input-group"><label for="phi">Variance design effect · φ</label><input id="phi" type="number" min="1" max="1000000" step="any" value="${planner.phi}"><small>1 = Poisson. Larger values inflate required miles. Uses VIN-year Pearson φ when one manufacturer is selected; not NB2 α.</small></div>
  <div class="input-group"><label for="allocation">Miles allocated to A <output id="allocation-value">${Math.round(planner.allocation*100)}%</output></label><input id="allocation" type="range" min="10" max="90" step="5" value="${planner.allocation*100}"></div>
  <div class="input-group"><label for="sidedness">Test direction</label><select id="sidedness">${options([['two','Two-sided'],['one','One-sided · reduction']],planner.twoSided?'two':'one')}</select></div><div class="input-group"><button id="refresh-baseline" class="small-button">↺ Use current selection</button></div></article>
  <div class="planner-right" id="planner-output" aria-live="polite"></div></div>`;
  ['baseline','reduction','power','alpha','phi','allocation','sidedness'].forEach(id=>{$(id).addEventListener(id==='reduction'||id==='allocation'?'input':'change',()=>{if(id==='sidedness')planner.twoSided=$(id).value==='two';else planner[id]=Number($(id).value)/(id==='allocation'?100:1);$('reduction-value').textContent=`${planner.reduction}%`;$('allocation-value').textContent=`${Math.round(planner.allocation*100)}%`;renderPlannerOutput();});});
  $('refresh-baseline').onclick=()=>{setPlannerBaseline();renderPlanner();};renderPlannerOutput();
}
function renderPlannerOutput() {
  try {
    const r=planner.baseline/1000,d=planner.reduction/100,result=plan(r,d,planner.alpha,planner.power,planner.phi,planner.allocation,planner.twoSided);
    if(!Number.isFinite(result.total_miles))throw new Error('The selected parameters exceed the numeric range.');
    const w=window.innerWidth<=760?390:650,h=245,l=48,right=22,t=20,b=42,max=result.total_miles*2,xx=m=>l+m/max*(w-l-right),yy=p=>h-b-p*(h-t-b);
    let chart=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Estimated power versus total miles"><title>Normal-approximate power by total exposure</title>`;
    for(let i=0;i<=4;i++){const p=i/4,y=yy(p);chart+=`<line x1="${l}" x2="${w-right}" y1="${y}" y2="${y}" stroke="#edf1e7"/><text x="${l-12}" y="${y+3}" text-anchor="end" font-size="9" fill="#596b5d">${p*100}%</text><text x="${xx(max*p)}" y="${h-20}" text-anchor="middle" font-size="9" fill="#596b5d">${compact(max*p)}</text>`;}
    let line='';for(let i=0;i<=100;i++){const m=max*i/100,p=powerAt(m,r,d,planner.alpha,planner.phi,planner.allocation,planner.twoSided);line+=`${i?'L':'M'}${xx(m)},${yy(p)} `;}
    chart+=`<path d="${line}L${xx(max)},${yy(0)} L${l},${yy(0)}Z" fill="#edf5e9"/><path d="${line}" stroke="#147d66" stroke-width="2.5" fill="none"/><path d="M${l},${yy(planner.power)}H${xx(result.total_miles)}V${yy(0)}" stroke="#bf915e" stroke-dasharray="4 4" fill="none"/><circle cx="${xx(result.total_miles)}" cy="${yy(planner.power)}" r="5" fill="#c88154" stroke="white" stroke-width="2"/><text x="${xx(result.total_miles)+12}" y="${yy(planner.power)-12}" fill="#596b5d" font-size="10">${planner.power*100}% target power</text><text x="${w/2}" y="${h-2}" text-anchor="middle" fill="#596b5d" font-size="8">TOTAL MILES · BOTH ARMS</text></svg>`;
    $('planner-output').innerHTML=`<article class="card planner-result"><div class="eyebrow">THE EXPOSURE YOUR QUESTION NEEDS</div><div class="big-number">${compact(result.total_miles)} <small>total miles</small></div><p>To detect a ${planner.reduction}% reduction with ${planner.power*100}% power, at α = ${planner.alpha}.</p><div class="arm-grid"><div><span>ARM A · BASELINE</span><strong>${compact(result.miles_a)} miles</strong><small>≈ ${fmt(result.events_a,0)} expected events</small></div><div><span>ARM B · ${planner.reduction}% REDUCTION</span><strong>${compact(result.miles_b)} miles</strong><small>≈ ${fmt(result.events_b,0)} expected events</small></div></div></article><article class="card"><h3>More miles. More power.</h3><p class="card-subtitle">The chance of detecting the specified reduction, if it exists.</p><div class="chart-frame">${chart}</div><p class="caption">Normal approximation using the alternative rate variance and constant design effect φ = ${fmt(planner.phi,2)}. Assumes independent arms, stable rates, and a prespecified test. The curve includes both tails for a two-sided test.</p></article><div class="warning">This is a hypothetical experiment, not a conclusion about DMV data. A VIN-year dispersion estimate is a sensitivity assumption, not a validated release-level design effect. Clustering, changing conditions, and sequential monitoring need a richer design.${Math.min(result.events_a,result.events_b)<20?' Expected event counts are small; the normal approximation may be unreliable.':''}</div>`;
  }catch(error){$('planner-output').innerHTML=`<div class="error-message" role="alert">${esc(error.message)}</div>`;}
}
function renderMethods() {
  $('view-methods').innerHTML=heading('04','Methods & data','The assumptions are part of the result.','Reproducible by design')+`<div class="method-grid">
  <article class="card method-card"><div class="method-number">01 / WHAT WE MEASURE</div><h3>A disengagement is an intervention.</h3><p>California DMV reports describe occasions when autonomous control disengages during testing. They are not collision reports, injuries, or a measure of crash prevention.</p><p>Intervention thresholds, testing difficulty, operating domains, and reporting practices differ. A lower reported rate does not establish that a company is safer.</p><div class="warning">Independent research project. No affiliation with or endorsement by Waymo, the DMV, or any manufacturer.</div></article>
  <article class="card method-card"><div class="method-number">02 / THE DENOMINATOR</div><h3>Exposure makes counts interpretable.</h3><p>Rates divide reported events by autonomous test miles. The period labeled 2024 covers December 1, 2023 through November 30, 2024.</p><p>Safety-driver and driverless permit reports stay separate. Testing mileage does not represent all commercial deployments or all operating conditions.</p><div class="formula">Observed rate = events ÷ autonomous miles<br>Model offset = log(autonomous miles)</div></article>
  <article class="card method-card"><div class="method-number">03 / RARE-EVENT UNCERTAINTY</div><h3>Exact bounds, including zero.</h3><p>The default count model is Poisson. Garwood’s two-sided exact interval uses chi-square quantiles with 2k and 2k + 2 degrees of freedom.</p><div class="formula">CI = [χ²(α/2, 2k), χ²(1−α/2, 2k+2)] / (2m)<br>k = 0: lower bound = 0</div><p>At zero events, the two-sided 95% upper bound is 3.689 ÷ miles. The separate one-sided 95% “rule of three” is 2.996 ÷ miles. Zero observed events does not imply zero underlying risk.</p></article>
  <article class="card method-card"><div class="method-number">04 / HETEROGENEITY</div><h3>When the Poisson model is too narrow.</h3><p>Auto checks VIN-year Pearson dispersion. If φ &gt; 1 and the asymptotic diagnostic p &lt; 0.05, it uses a converged NB2 model with at least three positive-exposure units.</p><div class="formula">E[Kᵢ] = milesᵢ × exp(β)<br>Var(Kᵢ) = μᵢ + αNB × μᵢ²</div><p>NB dispersion is estimated by maximum likelihood. Its interval is log-Wald, not exact. Non-identifiable fits explicitly fall back to Poisson. Sparse counts weaken the diagnostic; repeated VINs across years may remain correlated. NB intervals need not contain Poisson intervals, and the fitted rate may differ from the pooled rate.</p></article>
  <article class="card method-card"><div class="method-number">05 / COMPARISONS</div><h3>Association, not a release experiment.</h3><p>Compare displays B/A. Positive counts use a log-Wald interval, with standard error √(1/kA + 1/kB). An exact conditional binomial test evaluates equal Poisson rates, using p₀ = milesB / (milesA + milesB).</p><p>Zero-count comparisons use transformed Clopper–Pearson bounds without adding pseudo-events. Two zero-count groups do not identify a rate ratio. Group rates remain Poisson in this view.</p><p>These unadjusted comparisons do not account for multiple testing or confounding. A company-year is not a randomized software release.</p></article>
  <article class="card method-card"><div class="method-number">06 / EXPERIMENT DESIGN</div><h3>Plan in miles. Think in events.</h3><p>For rates rA and rB, allocation f to arm A, and constant design effect φ, the planner uses a normal approximation to the difference in independent rates.</p><div class="formula">T = φ (zcrit + zpower)²<br> × [rA/f + rB/(1−f)] / (rA−rB)²</div><p>T is total miles across both arms. φ is a quasi-Poisson variance multiplier, not NB2 α. Expected events are rate × miles for each arm. With a baseline of 1 per 1,000 miles, 10% reduction, 80% power, 5% two-sided α, φ = 1 and equal allocation: about 2.983 million total miles.</p></article>
  <article class="card method-card method-wide"><div class="card-title"><div><div class="method-number">07 / SOURCE AUDIT</div><h3>Real data. Visible imperfections.</h3></div><span class="mini-badge">2020–2024 SNAPSHOT</span></div><div class="quality-grid"><div><strong>14</strong><span>Original DMV source files</span></div><div><strong>22,958</strong><span>Detailed disengagement records</span></div><div><strong>128 / 128</strong><span>Annual event totals reconciled</span></div></div><p>This versioned historical snapshot was retrieved September 16, 2026 UTC. It is not a live feed or a claim to include the latest reporting year. Raw file URLs, timestamps, and SHA-256 hashes are recorded in the manifest.</p><ul class="audit-list"><li>47 missing annual mileage cells were reconstructed from reported monthly values.</li><li>13 unparseable or out-of-period event dates are flagged and retained under the source reporting year.</li><li>One VIN reports events with zero mileage. Affected groups fall back to aggregate Poisson instead of fitting a different count.</li><li>Blank spreadsheet rows were removed, corporate aliases normalized, and zero-event vehicles retained.</li><li>All 128 annual event totals match the detailed event counts. No synthetic data is loaded.</li></ul><div class="source-links"><a href="https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/" target="_blank" rel="noopener">California DMV ↗</a><a href="/waymo-project/sources.json" download>↓ Source manifest</a><a href="/waymo-project/exposure.csv" download>↓ Annual data</a><a href="/waymo-project/audit.csv" download>↓ Audit log</a><a href="https://github.com/kushal-acharya/av-safety-rate-explorer" target="_blank" rel="noopener">Code, tests & Python app ↗</a></div><p class="caption">References: Garwood (1936), Biometrika 28:437–442; McCullagh & Nelder (1989), Generalized Linear Models; statsmodels NegativeBinomial (NB2); SciPy chi-square and binomial inference. All statistical calculations are checked against the Python reference implementation.</p></article></div>`;
}
function render() {
  if(!data)return;
  refreshFilters(); updateURL();
  document.querySelectorAll('.nav-item').forEach(el=>{el.classList.toggle('active',el.dataset.tab===state.tab);if(el.dataset.tab===state.tab)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
  for(const tab of ['rates','compare','planner','methods'])$(`view-${tab}`).hidden=tab!==state.tab;
  ({rates:renderRates,compare:renderCompare,planner:renderPlanner,methods:renderMethods})[state.tab]();
}
function reset() { Object.assign(state,{companies:['Waymo'],years:[2020,2021,2022,2023,2024],mode:'safety-driver',confidence:.95,unit:1000,method:'auto'});plannerInitialized=false;render(); }
document.addEventListener('click',e=>{
  const tab=e.target.closest('[data-tab]');if(tab){setTab(tab.dataset.tab);return;}
  const year=e.target.closest('[data-year]');if(year){const y=Number(year.dataset.year);state.years=state.years.includes(y)?state.years.filter(x=>x!==y):[...state.years,y].sort();render();return;}
  if(e.target.closest('[data-reset]'))reset();
  if(!e.target.closest('#company-picker'))$('company-picker').open=false;
});
$('company-options').addEventListener('change',e=>{const name=e.target.value;state.companies=e.target.checked?[...state.companies,name]:state.companies.filter(x=>x!==name);render();});
$('all-companies').onclick=()=>{state.companies=[...new Set(data.annual.map(r=>r.manufacturer))].sort();render();};
$('clear-companies').onclick=()=>{state.companies=[];render();};
$('mode').onchange=e=>{state.mode=e.target.value;if(state.mode==='driverless'){state.years=state.years.filter(y=>y>=2023);if(!state.years.length)state.years=[2023,2024];}render();};
$('confidence').onchange=e=>{state.confidence=Number(e.target.value);render();};
$('reset').onclick=reset;
$('share').onclick=async()=>{try{await navigator.clipboard.writeText(location.href);toast('Link copied — your filters travel with it.');}catch{toast('Copy the current address to share these filters.');}};
fetch('/waymo-project/data.json').then(r=>{if(!r.ok)throw new Error('Snapshot could not be loaded.');return r.json();}).then(d=>{data=d;state.companies=state.companies.filter(c=>d.annual.some(r=>r.manufacturer===c));$('loading').hidden=true;render();}).catch(e=>{$('loading').textContent=`${e.message} Reload to try again, or download the source data from GitHub.`;});

matchMedia('(max-width:760px)').addEventListener('change',()=>{if(data)render();});
