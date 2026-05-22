#!/usr/bin/env node
// Checks that README screenshot references are covered by generated verifier
// candidates and committed docs/screenshots assets.
import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { basename, join } from "node:path";
import { spawnSync } from "node:child_process";
import { inflateSync } from "node:zlib";

const readmePath = "README.md";
const docsDir = "docs/screenshots";
const candidateDirs = [
  ".verify/screenshots/readme",
  ".verify/screenshots/legacy",
];
const PNG_SIGNATURE = Buffer.from([
  0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a,
]);
const isCI = process.env.CI === "true" || process.env.GITHUB_ACTIONS === "true";
const strictScreenshotDiffs =
  process.env.PROMPTEER_STRICT_README_SCREENSHOTS === "1" || !isCI;
const MAX_CHANNEL_DELTA = isCI ? 32 : 1;
const MAX_CHANGED_PIXEL_RATIO = isCI ? 0.04 : 0.006;
const MAX_NORMALIZED_RMSE = isCI ? 0.015 : 0.0003;

function pngFilesIn(directory) {
  if (!existsSync(directory)) {
    return [];
  }
  return readdirSync(directory)
    .filter((name) => name.endsWith(".png"))
    .sort();
}

function readmeScreenshotNames() {
  const readme = readFileSync(readmePath, "utf8");
  return [
    ...new Set(
      [...readme.matchAll(/docs\/screenshots\/([^)\s]+\.png)/g)].map(
        (match) => match[1],
      ),
    ),
  ].sort();
}

function trackedScreenshotNames() {
  const result = spawnSync("git", ["ls-files", `${docsDir}/*.png`], {
    encoding: "utf8",
  });
  if (result.status !== 0) {
    throw new Error(result.stderr || "git ls-files failed");
  }
  return result.stdout
    .split("\n")
    .filter(Boolean)
    .filter((path) => existsSync(path))
    .map((path) => basename(path))
    .sort();
}

function generatedScreenshotNames() {
  return [
    ...new Set(candidateDirs.flatMap((directory) => pngFilesIn(directory))),
  ].sort();
}

function setDiff(left, right) {
  const rightSet = new Set(right);
  return left.filter((item) => !rightSet.has(item));
}

function hash(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function paethPredictor(left, up, upLeft) {
  const estimate = left + up - upLeft;
  const leftDistance = Math.abs(estimate - left);
  const upDistance = Math.abs(estimate - up);
  const upLeftDistance = Math.abs(estimate - upLeft);
  if (leftDistance <= upDistance && leftDistance <= upLeftDistance) {
    return left;
  }
  if (upDistance <= upLeftDistance) {
    return up;
  }
  return upLeft;
}

function decodePng(path) {
  const file = readFileSync(path);
  if (!file.subarray(0, PNG_SIGNATURE.length).equals(PNG_SIGNATURE)) {
    throw new Error(`${path} is not a PNG file`);
  }

  let offset = PNG_SIGNATURE.length;
  let width = 0;
  let height = 0;
  let bitDepth = 0;
  let colorType = 0;
  let interlaceMethod = 0;
  const idatChunks = [];

  while (offset < file.length) {
    const length = file.readUInt32BE(offset);
    const type = file.toString("ascii", offset + 4, offset + 8);
    const dataStart = offset + 8;
    const dataEnd = dataStart + length;
    const data = file.subarray(dataStart, dataEnd);

    if (type === "IHDR") {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      bitDepth = data[8];
      colorType = data[9];
      interlaceMethod = data[12];
    } else if (type === "IDAT") {
      idatChunks.push(data);
    } else if (type === "IEND") {
      break;
    }

    offset = dataEnd + 4;
  }

  const channels = colorType === 6 ? 4 : colorType === 2 ? 3 : 0;
  if (bitDepth !== 8 || channels === 0 || interlaceMethod !== 0) {
    throw new Error(
      `${path} uses unsupported PNG encoding bitDepth=${bitDepth} colorType=${colorType} interlace=${interlaceMethod}`,
    );
  }

  const stride = width * channels;
  const raw = inflateSync(Buffer.concat(idatChunks));
  const pixels = Buffer.alloc(width * height * channels);
  let inputOffset = 0;
  let outputOffset = 0;
  let previousRow = Buffer.alloc(stride);

  for (let y = 0; y < height; y += 1) {
    const filter = raw[inputOffset];
    inputOffset += 1;
    const row = Buffer.from(raw.subarray(inputOffset, inputOffset + stride));
    inputOffset += stride;

    for (let x = 0; x < stride; x += 1) {
      const left = x >= channels ? row[x - channels] : 0;
      const up = previousRow[x] ?? 0;
      const upLeft = x >= channels ? previousRow[x - channels] : 0;

      if (filter === 1) {
        row[x] = (row[x] + left) & 0xff;
      } else if (filter === 2) {
        row[x] = (row[x] + up) & 0xff;
      } else if (filter === 3) {
        row[x] = (row[x] + Math.floor((left + up) / 2)) & 0xff;
      } else if (filter === 4) {
        row[x] = (row[x] + paethPredictor(left, up, upLeft)) & 0xff;
      } else if (filter !== 0) {
        throw new Error(`${path} uses unsupported PNG filter ${filter}`);
      }
    }

    row.copy(pixels, outputOffset);
    outputOffset += stride;
    previousRow = row;
  }

  return { width, height, channels, pixels };
}

function imageDifference(leftPath, rightPath) {
  const left = decodePng(leftPath);
  const right = decodePng(rightPath);

  if (
    left.width !== right.width ||
    left.height !== right.height ||
    left.channels !== right.channels
  ) {
    return {
      comparable: false,
      reason: `dimension/channel mismatch ${left.width}x${left.height}x${left.channels} vs ${right.width}x${right.height}x${right.channels}`,
    };
  }

  let sumSquares = 0;
  let maxChannelDelta = 0;
  let changedPixels = 0;
  const pixelCount = left.width * left.height;

  for (let pixel = 0; pixel < pixelCount; pixel += 1) {
    let pixelChanged = false;
    const base = pixel * left.channels;
    for (let channel = 0; channel < left.channels; channel += 1) {
      const delta = Math.abs(
        left.pixels[base + channel] - right.pixels[base + channel],
      );
      if (delta > 0) {
        pixelChanged = true;
        sumSquares += delta * delta;
        maxChannelDelta = Math.max(maxChannelDelta, delta);
      }
    }
    if (pixelChanged) {
      changedPixels += 1;
    }
  }

  return {
    comparable: true,
    changedPixelRatio: changedPixels / pixelCount,
    maxChannelDelta,
    normalizedRmse: Math.sqrt(sumSquares / left.pixels.length) / 255,
  };
}

function isEquivalentScreenshot(docsPath, candidatePath) {
  if (hash(docsPath) === hash(candidatePath)) {
    return { equivalent: true, exact: true };
  }

  const difference = imageDifference(docsPath, candidatePath);
  if (!difference.comparable) {
    return { equivalent: false, exact: false, difference };
  }

  const equivalent =
    difference.maxChannelDelta <= MAX_CHANNEL_DELTA &&
    difference.changedPixelRatio <= MAX_CHANGED_PIXEL_RATIO &&
    difference.normalizedRmse <= MAX_NORMALIZED_RMSE;

  return { equivalent, exact: false, difference };
}

function candidatePathFor(name) {
  for (const directory of candidateDirs) {
    const path = join(directory, name);
    if (existsSync(path)) {
      return path;
    }
  }
  return null;
}

function githubEscape(value) {
  return String(value)
    .replaceAll("%", "%25")
    .replaceAll("\r", "%0D")
    .replaceAll("\n", "%0A");
}

function annotate(level, message) {
  if (process.env.GITHUB_ACTIONS !== "true") {
    return;
  }
  console.error(`::${level}::${githubEscape(message)}`);
}

function assertSameSet(label, expected, actual, failures) {
  const missing = setDiff(expected, actual);
  const extra = setDiff(actual, expected);
  if (missing.length > 0 || extra.length > 0) {
    failures.push(
      `${label} mismatch: missing=[${missing.join(", ")}] extra=[${extra.join(", ")}]`,
    );
  }
}

const readmeNames = readmeScreenshotNames();
const trackedNames = trackedScreenshotNames();
const generatedNames = generatedScreenshotNames();
const failures = [];

assertSameSet(
  "tracked docs/screenshots vs README",
  readmeNames,
  trackedNames,
  failures,
);
assertSameSet(
  "generated verifier candidates vs README",
  readmeNames,
  generatedNames,
  failures,
);

const changed = [];
const tolerated = [];
for (const name of readmeNames) {
  const docsPath = join(docsDir, name);
  const candidatePath = candidatePathFor(name);
  if (!candidatePath || !existsSync(docsPath)) {
    continue;
  }
  const comparison = isEquivalentScreenshot(docsPath, candidatePath);
  if (!comparison.equivalent) {
    changed.push({ name, difference: comparison.difference });
  } else if (!comparison.exact) {
    tolerated.push({ name, difference: comparison.difference });
  }
}

if (changed.length > 0) {
  for (const { name, difference } of changed) {
    const detail = difference.comparable
      ? `maxChannelDelta=${difference.maxChannelDelta}, changedPixelRatio=${difference.changedPixelRatio.toFixed(6)}, normalizedRmse=${difference.normalizedRmse.toFixed(6)}`
      : difference.reason;
    annotate(
      strictScreenshotDiffs ? "error" : "warning",
      `README screenshot candidate differs for ${name}: ${detail}`,
    );
  }
  const changedSummary = `README screenshot candidates differ from committed docs assets: ${changed.map(({ name }) => name).join(", ")}`;
  const reviewHint =
    "Review .verify/screenshots/readme and .verify/screenshots/legacy, then run make update-ui-screenshots to promote approved images.";
  if (strictScreenshotDiffs) {
    failures.push(changedSummary);
    failures.push(reviewHint);
  } else {
    console.warn(`${changedSummary}\n${reviewHint}`);
    console.warn(
      "CI treats screenshot pixel drift as advisory because GitHub-hosted Linux rendering can differ from curated local README captures. Set PROMPTEER_STRICT_README_SCREENSHOTS=1 to fail CI on pixel drift.",
    );
  }
}

if (failures.length > 0) {
  console.error(failures.join("\n"));
  process.exit(1);
}

for (const { name, difference } of tolerated) {
  console.warn(
    `Accepted tiny screenshot render delta for ${name}: maxChannelDelta=${difference.maxChannelDelta}, changedPixelRatio=${difference.changedPixelRatio.toFixed(6)}, normalizedRmse=${difference.normalizedRmse.toFixed(6)}`,
  );
}

console.log(
  `Verified README screenshot coverage: ${readmeNames.length} referenced, ${trackedNames.length} tracked, ${generatedNames.length} generated.`,
);
