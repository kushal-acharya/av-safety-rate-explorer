import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spatialScenario} from '../web-src/geography.js';
const study = JSON.parse(readFileSync(new URL('../web/waymo-project/geography.json', import.meta.url)));
test('135 spatial scenarios agree with the independent Python calculations', () => {
  for (const row of study.comparisons) for (const expected of row.scenarios) {
    const actual = spatialScenario(row, expected.mix, expected.stress);
    for (const key of Object.keys(actual)) assert.ok(Math.abs(actual[key]-expected[key]) < 1e-8*Math.max(1,Math.abs(expected[key])), `${row.city}/${row.metric}/${key}`);
  }
});
test('invalid spatial sensitivity settings are rejected', () => {
  for (const [mix, stress] of [[-1,1],[2,1],[NaN,1],[1,0],[1,Infinity]])
    assert.throws(()=>spatialScenario(study.comparisons[0],mix,stress));
});
