import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { contextRows } from '../web-src/context.js';
const data = JSON.parse(fs.readFileSync(new URL('../web/waymo-project/data.json', import.meta.url)));

test('every context reconciles for every annual cell and preserves its full exposure',()=>{
  for(const annual of data.annual.filter(r=>r.eligible)) {
    for(const dimension of Object.keys(data.context_categories)) {
      const rows=contextRows(data,[annual],dimension);
      assert.equal(rows.reduce((n,r)=>n+r.events,0),annual.events);
      assert.ok(rows.every(r=>r.miles===annual.miles&&r.upper>0&&r.lower>=0));
      if(annual.events)assert.ok(Math.abs(rows.reduce((n,r)=>n+r.share,0)-1)<1e-12);
      else assert.ok(rows.every(r=>r.share===null));
    }
  }
});
test('pooled context respects mode and year selection and retains zero categories',()=>{
  const selected=data.annual.filter(r=>r.eligible&&r.mode==='driverless'&&r.year===2024&&r.manufacturer==='Waymo');
  const rows=contextRows(data,selected,'initiated_by',.99);
  assert.equal(rows.reduce((n,r)=>n+r.events,0),22);
  assert.equal(rows.length,5);
  assert.ok(rows.some(r=>r.events===0&&r.upper>0));
  const eligible=data.annual.filter(r=>r.eligible&&r.mode==='safety-driver');
  const all=contextRows(data,eligible,'location');
  assert.equal(all.reduce((n,r)=>n+r.events,0),eligible.reduce((n,r)=>n+r.events,0));
});
test('empty selection and unrecognized context have explicit behavior',()=>{
  assert.deepEqual(contextRows(data,[],'location'),[]);
  assert.throws(()=>contextRows(data,[],'not-a-dimension'));
});
