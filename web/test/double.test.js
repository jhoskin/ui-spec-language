// The reference service double must give the replies in fixture/vectors.json.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { runVector } from "../../tools/make-vectors.mjs";

const { vectors } = JSON.parse(readFileSync(new URL("../../fixture/vectors.json", import.meta.url)));
for (const v of vectors) {
  test(`vector: ${v.name}`, () => assert.deepEqual(runVector(v), v.replies));
}
