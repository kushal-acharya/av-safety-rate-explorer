/** Review the standalone brief, its research links and responsive presentation. */
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import AxeBuilder from '@axe-core/playwright';
const browser=await chromium.launch({headless:true,channel:process.env.CI?undefined:'chrome'});
const origin=process.env.AV_TEST_ORIGIN||'http://localhost:8789';
const noScript=await browser.newPage({javaScriptEnabled:false});
await noScript.goto(`${origin}/waymo-project/brief.html`);
assert.equal(await noScript.locator('.tour-card').count(),3);
await noScript.close();
const context=await browser.newContext({viewport:{width:1440,height:1100}});
const page=await context.newPage();
try {
  const response=await page.goto(`${origin}/waymo-project/brief.html`,{waitUntil:'networkidle'});
  assert.equal(response.status(),200);
  assert.equal(await page.locator('h1').count(),1);
  assert.equal(await page.locator('.tour-card').count(),3);
  for(const width of [1440,768,390,320]) {
    await page.setViewportSize({width,height:1000});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`brief overflow at ${width}`);
    assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[]);
  }
  await page.setViewportSize({width:1440,height:1100});await page.screenshot({path:'assets/brief.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:'assets/brief-mobile.png',fullPage:true});
  const links=await page.locator('.card-link').evaluateAll(els=>els.map(el=>el.href));
  const live=await browser.newPage();
  for(const [i,selector] of ['#study-audit-table','#geo-audit-table','#planner-output'].entries()) {
    await live.goto(links[i],{waitUntil:'networkidle'});await live.locator(selector).waitFor();
    assert.equal(await live.locator('.brief-entry').getAttribute('href'),'/waymo-project/brief.html');
  }
  console.log('Project brief passes: no-JavaScript rendering, four viewport sizes, accessibility and all three live research entry points.');
} finally {await browser.close();}
