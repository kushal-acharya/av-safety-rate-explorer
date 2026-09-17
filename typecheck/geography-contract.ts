// Compile-time contract against the real exported snapshot, never executed.
import snapshot from "../web/waymo-project/geography.json";
import { spatialScenario } from "../web-src/geography.js";
import { renderReadingGuide } from "../web-src/geography-guide.js";
import type {
  GeographySnapshot,
  SpatialScenario,
} from "../web-src/geography-types";
const checked: GeographySnapshot = snapshot;
const row = checked.comparisons[0];
const result: SpatialScenario = spatialScenario(row, 0.5, 1);
const guide: string = renderReadingGuide(row, result, false);
void guide;
// @ts-expect-error Rates cannot be strings.
spatialScenario({ ...row, baseline_ipmm: "5.82" });
// @ts-expect-error Every result must contain uncertainty endpoints.
const incomplete: SpatialScenario = { ratio: 0.1 };
void incomplete;
// @ts-expect-error Mix is a number, not a UI string.
spatialScenario(row, "50");
