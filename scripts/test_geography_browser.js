/** Verify geographic evidence, source invariance, continuous controls and share links. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';
import { spatialScenario } from '../web-src/geography.js';
const origin=process.env.AV_TEST_ORIGIN||'http://localhost:8789';
const study=JSON.parse(await readFile('web/waymo-project/geography.json','utf8'));
const browser=await chromium.launch({headless:true,channel:process.env.CI?undefined:'chrome'});
const page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[];
page.on('pageerror',error=>errors.push(error.message));
try {
 await page.goto(`${origin}/waymo-project/?tab=geography&confidence=0.99&companies=Zoox`,{waitUntil:'networkidle'});
 await page.locator('#geo-audit-table').waitFor();
 assert.equal(await page.locator('.filters').isVisible(),false);
 for(const row of study.comparisons) {
  await page.selectOption('#geo-city',row.city);await page.selectOption('#geo-metric',row.metric);
  assert.equal(await page.locator('#geo-reduction').innerText(),`${row.matched.reduction_percent.toFixed(1)}%`);
  assert.equal(await page.locator('#geo-audit-table tbody tr').count(),3);
  const audit=await page.locator('#geo-audit-table').innerText();
  for(const [mix,stress] of [[0,100],[37,78],[100,150]]) {
   for(const [id,value] of [['geo-mix',mix],['geo-stress',stress]]) await page.locator(`#${id}`).evaluate((el,value)=>{el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));},value);
   const expected=spatialScenario(row,mix/100,stress/100);
   assert.equal(await page.locator('#geo-reduction').innerText(),`${expected.reduction_percent.toFixed(1)}%`);
   assert.equal(await page.locator('#geo-ratio').innerText(),expected.ratio.toFixed(4));
   assert.equal(await page.locator('#geo-audit-table').innerText(),audit);
  }
  await page.click('#geo-reset');
 }
 await page.selectOption('#geo-city','PHOENIX');await page.selectOption('#geo-metric','observed_any_injury');
 await page.locator('#geo-mix').focus();await page.keyboard.press('ArrowLeft');
 assert.equal(await page.locator('#geo-mix').inputValue(),'99');
 await page.keyboard.press('ArrowLeft');assert.equal(await page.locator('#geo-mix').inputValue(),'98');
 assert.equal(await page.locator('#geo-mix').evaluate(el=>el===document.activeElement),true);
 await page.reload({waitUntil:'networkidle'});await page.locator('#geo-audit-table').waitFor();
 assert.equal(await page.locator('#geo-city').inputValue(),'PHOENIX');
 assert.equal(await page.locator('#geo-metric').inputValue(),'observed_any_injury');
 assert.equal(await page.locator('#geo-mix').inputValue(),'98');
 for(const [file,rows] of [['cells',2962],['events',524],['inputs',10],['results',10]]) {
  const download=page.waitForEvent('download');await page.locator(`a[download][href="/waymo-project/geography-${file}.csv"]`).click();
  const saved=await download;const text=await readFile(await saved.path(),'utf8');assert.equal(text.trim().split('\n').length,rows);
 }
 await page.selectOption('#geo-city','SAN_FRANCISCO');await page.selectOption('#geo-metric','airbag');await page.click('#geo-reset');
 await page.screenshot({path:'assets/geography.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:'assets/geography-mobile.png',fullPage:true});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'mobile overflow');
 await page.click('.nav-item[data-tab="rates"]');assert.equal(await page.locator('.filters').isVisible(),true);
 assert.equal(await page.locator('#confidence').inputValue(),'0.99');
 await page.route('**/geography.json',route=>route.fulfill({status:503,body:'Unavailable'}));
 await page.goto(`${origin}/waymo-project/?tab=geography`,{waitUntil:'networkidle'});await page.locator('#geo-retry').waitFor();
 await page.unroute('**/geography.json');await page.click('#geo-retry');await page.locator('#geo-audit-table').waitFor();
 await page.goto(`${origin}/waymo-project/?tab=geography&geoCity=INVALID&geoMetric=INVALID&geoMix=NaN&geoStress=-4`,{waitUntil:'networkidle'});
 await page.locator('#geo-audit-table').waitFor();assert.equal(await page.locator('#geo-city').inputValue(),'SAN_FRANCISCO');assert.equal(await page.locator('#geo-stress').inputValue(),'100');
 assert.deepEqual(errors,[]);
 console.log('Geography browser checks pass: all nine comparisons, controls, invariant audit, share state, exports, mobile, invalid URL and retry.');
} finally {await browser.close();}
