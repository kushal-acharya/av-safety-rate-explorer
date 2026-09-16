/** Check the scientific UI, URL state, isolation, exports and recoverable data failures. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';
const origin = process.env.AV_TEST_ORIGIN || 'http://localhost:8789';
const study = JSON.parse(await readFile('web/waymo-project/replication.json', 'utf8'));
const browser = await chromium.launch({headless:true, channel:process.env.CI ? undefined : 'chrome'});
const page = await browser.newPage({viewport:{width:1440,height:1100}});
const errors = [];
page.on('pageerror', error => errors.push(error.message));
try {
  await page.goto(`${origin}/waymo-project/?tab=replication&confidence=0.99&companies=Zoox&years=2024`, {waitUntil:'networkidle'});
  await page.locator('#study-audit-table').waitFor();
  assert.equal(await page.locator('.filters').isVisible(), false);
  assert.equal(await page.locator('.hero').isVisible(), false);
  assert.equal(await page.locator('.study-headline').innerText(), '90.2%');
  assert.equal(await page.locator('#study-paper').getAttribute('aria-pressed'), 'true');
  for (const row of study.comparisons) {
    await page.selectOption('#study-comparison', row.id);
    await page.waitForFunction(id => new URLSearchParams(location.search).get('study') === id, row.id);
    assert.equal(await page.locator('#study-audit-table tbody tr').count(), 4);
    const values = await page.locator('#study-audit-table tbody tr').evaluateAll(rows => rows.map(row => row.cells[2].textContent));
    assert.equal(Number(values[0]), row.events);
    assert.equal(values[1], row.paper_code.ratio.toFixed(6));
    assert.equal(values[2], row.paper_code.lower.toFixed(6));
    assert.equal(values[3], row.paper_code.upper.toFixed(6));
    await page.click('#study-equation');
    assert.equal(await page.locator('#study-equation').getAttribute('aria-pressed'), 'true');
    assert.ok((await page.locator('.study-result-details').innerText()).includes(row.equation.upper.toFixed(4)));
    assert.ok((await page.locator('#study-audit-table').innerText()).includes(row.paper_code.upper.toFixed(6)), 'audit must retain paper-code values');
    if (row.id === 'phx-injury') {
      assert.match(await page.locator('.study-conclusion').innerText(), /excludes equal rates/);
      await page.click('#study-paper');
      assert.match(await page.locator('.study-conclusion').innerText(), /includes equal rates/);
    }
    await page.click('#study-paper');
  }
  await page.selectOption('#study-comparison','phx-injury');
  await page.click('#study-equation');
  await page.reload({waitUntil:'networkidle'});
  await page.locator('#study-audit-table').waitFor();
  assert.equal(await page.locator('#study-comparison').inputValue(),'phx-injury');
  assert.equal(await page.locator('#study-equation').getAttribute('aria-pressed'),'true');
  for (const [name, rows] of [['results',17], ['events',74], ['inputs',5]]) {
    const download = page.waitForEvent('download');
    await page.locator(`a[download][href="/waymo-project/replication-${name}.csv"]`).click();
    const file = await download;
    const content = await readFile(await file.path(), 'utf8');
    assert.equal(content.trim().split('\n').length, rows);
  }
  await page.selectOption('#study-comparison','sf-injury');
  await page.click('#study-paper');
  await page.screenshot({path:'assets/replication.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:'assets/replication-mobile.png',fullPage:true});
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),'study mobile overflow');
  await page.click('#study-equation');
  assert.equal(await page.locator('#study-equation').getAttribute('aria-pressed'),'true');
  await page.click('.nav-item[data-tab="rates"]');
  assert.equal(await page.locator('.filters').isVisible(),true);
  assert.equal(await page.locator('#confidence').inputValue(),'0.99');
  // A failed study request should not trap the app, and Retry should recover.
  await page.route('**/replication.json',route => route.fulfill({status:503,body:'Unavailable'}));
  await page.goto(`${origin}/waymo-project/?tab=replication`,{waitUntil:'networkidle'});
  await page.locator('#study-retry').waitFor();
  await page.unroute('**/replication.json');
  await page.click('#study-retry');
  await page.locator('#study-audit-table').waitFor();
  assert.deepEqual(errors,[]);
  console.log('Study browser checks pass: all four calculations, both conventions, stable audit, URL, filter isolation, downloads, mobile and retry.');
} finally { await browser.close(); }
