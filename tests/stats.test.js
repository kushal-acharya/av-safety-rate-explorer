import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {poisson,ratio,plan,powerAt,zeroBound,interval} from '../web-src/stats.js';
const refs=JSON.parse(fs.readFileSync(new URL('./reference.json',import.meta.url)));
const close=(a,b,label)=>assert.ok(Math.abs(a-b)<=Math.max(1e-10,Math.abs(b)*2e-6),`${label}: ${a} != ${b}`);
for(const [name,fn] of Object.entries({poisson,ratio,plan,power:powerAt})) {
  test(`${name} agrees with independent Python reference vectors`,()=>{
    for(const {args,result} of refs[name]) {
      const actual=fn(...args);
      if(typeof result==='number'){close(actual,result,name);continue;}
      for(const [key,value] of Object.entries(result)) {
        if(typeof value==='number')close(actual[key],value,`${name} ${args} ${key}`);
        else if(value===null)assert.equal(actual[key],null);
      }
    }
  });
}
test('zero-event conventions and model fallback',()=>{
  close(zeroBound(1000),2.995732273553991/1000,'rule of three');
  const r=interval({events:0,miles:1000},{method:'Negative binomial',rate:0,log_se:1},'nb',.05);
  assert.equal(r.method,'Poisson exact');assert.ok(r.upper>0);
  assert.ok(interval({events:5,miles:1000},{warning:'Fit failed'},'nb',.05).warning);
});
test('bad inputs fail explicitly',()=>{
  for(const fn of [()=>poisson(-1,1),()=>poisson(.2,1),()=>poisson(1,0),()=>poisson(1,1,0),()=>zeroBound(0),()=>plan(0,.1),()=>plan(.001,0),()=>plan(.001,.1,.05,.8,0),()=>powerAt(-1,.001,.1)])assert.throws(fn);
});
