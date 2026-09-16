import { contextRows } from './context.js';

const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number = (value, digits = 3) => value.toLocaleString('en-US', {maximumFractionDigits: digits});
const rate = value => value > 0 && value < .001 ? value.toExponential(2) : number(value, value < .1 ? 4 : 3);
const labels = {initiated_by: 'Disengagement initiator', location: 'Reported location', cause_category: 'Cause keyword category'};
const colors = ['#096c5c','#438b74','#729f85','#acbda0','#bd835c','#cbb990','#9aa39b'];

export function mountEventContext(container, {data, annualRows, dimension, confidence, unit, onDimension}) {
  const rows = contextRows(data, annualRows, dimension, confidence);
  const total = rows.reduce((sum,row)=>sum+row.events,0);
  const miles = rows[0]?.miles ?? 0;
  const confidenceLabel = `${Math.round(confidence*100)}%`;
  const explanation = dimension === 'cause_category'
    ? 'Cause labels are first-match keyword buckets, not validated root causes. Negation and boilerplate can misclassify a report.'
    : dimension === 'location'
      ? 'Street, freeway and other categories describe where events occurred. Mileage by road type is unavailable. “Urban” and “Express Way” remain Unknown because they do not uniquely identify the listed road classes.'
      : 'Known aliases are grouped. Ambiguous entries such as “Yes”, “Operator”, “In-Field Retrieval” and mixed driver/system responses remain Unknown. Original labels are preserved in the source records.';
  container.innerHTML=`<div class="card-title"><div><span class="insight-kicker">LOOK INSIDE THE COUNTS</span><h3>Inside the reported events</h3><p class="card-subtitle">${number(total,0)} events · ${number(miles,1)} total selected miles</p></div><div class="context-select"><label for="context-dimension">Explore by</label><select id="context-dimension">${Object.entries(labels).map(([key,value])=>`<option value="${key}" ${key===dimension?'selected':''}>${value}</option>`).join('')}</select></div></div>
  <p class="context-explanation">${explanation}</p>
  ${total?`<div class="breakdown" aria-hidden="true">${rows.map((row,i)=>`<span style="width:${row.share*100}%;background:${colors[i]}"></span>`).join('')}</div>`:'<p class="warning">No events were reported in this selection. Event shares are undefined; each category still has a positive upper rate bound.</p>'}
  <div class="table-wrap"><table id="context-table"><caption class="sr-only">Event context: ${labels[dimension]}, rates per ${number(unit,0)} total selected miles, ${confidenceLabel} exact Poisson confidence intervals</caption><thead><tr><th scope="col">CATEGORY</th><th scope="col" class="num">EVENTS</th><th scope="col" class="num">SHARE OF EVENTS</th><th scope="col" class="num">RATE / ${number(unit,0)} TOTAL MI</th><th scope="col" class="num">${confidenceLabel} EXACT CI</th></tr></thead><tbody>${rows.map((row,i)=>`<tr><th scope="row"><span class="context-dot" style="background:${colors[i]}"></span>${escape(row.category)}</th><td class="num">${number(row.events,0)}</td><td class="num">${row.share===null?'—':number(row.share*100,1)+'%'}</td><td class="num">${row.events?rate(row.rate*unit):'Upper bound only'}</td><td class="num">${rate(row.lower*unit)}–${rate(row.upper*unit)}</td></tr>`).join('')}</tbody></table></div>
  <div class="context-footer"><p class="caption"><strong>Same denominator, every row.</strong> Category rates use all ${number(miles,1)} selected miles, not category-specific mileage. Intervals are exact Poisson, independent of the main chart’s interval setting. Unknown and zero-event categories are retained.</p><button id="context-export" class="small-button">↓ Export context</button></div>`;
  container.querySelector('#context-dimension').onchange=e=>onDimension(e.target.value);
  container.querySelector('#context-export').onclick=()=>{
    const headers=['dimension','category','events','share_of_reported_events','total_exposure_miles','rate_per_mile','lower_per_mile','upper_per_mile','confidence','method','zero_event_upper_bound_only','mode','manufacturers','reporting_years'];
    const modes=[...new Set(annualRows.map(r=>r.mode))].join(';');
    const companies=[...new Set(annualRows.map(r=>r.manufacturer))].sort().join(';');
    const years=[...new Set(annualRows.map(r=>r.year))].sort().join(';');
    const csv=[headers.join(','),...rows.map(r=>[dimension,r.category,r.events,r.share,r.miles,r.events?r.rate:null,r.lower,r.upper,confidence,r.method,!r.events,modes,companies,years].map(v=>v===null?'':JSON.stringify(v)).join(','))].join('\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
    const link=document.createElement('a');link.href=url;link.download='av-evidence-event-context.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
}
