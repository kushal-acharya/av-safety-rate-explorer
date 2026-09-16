import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
const browser=await chromium.launch({headless:true,channel:process.env.CI?undefined:'chrome'});
const context=await browser.newContext({viewport:{width:1440,height:1100}});
const page=await context.newPage();
try {
  for(const tab of ['rates','compare','planner','methods']) {
    await page.goto(`${process.env.AV_TEST_ORIGIN||'http://localhost:8789'}/waymo-project/?tab=${tab}`,{waitUntil:'networkidle'});
    const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
    const errors=result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}));
    console.log(tab,JSON.stringify(errors));
    assert.deepEqual(errors,[],`${tab} accessibility violations`);
  }
  console.log('All four views pass the automated WCAG A/AA scan.');
} finally {await browser.close();}
