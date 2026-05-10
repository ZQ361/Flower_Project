import { mkdir, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const publicDir = path.resolve(__dirname, "..");
const projectRoot = path.resolve(publicDir, "..", "..");

const catalogPath = path.join(projectRoot, "backend", "app", "data", "flowers_102_zh.json");
const outputDir = path.join(publicDir, "plants", "images");
const creditsPath = path.join(publicDir, "plants", "credits.json");
const reviewPath = path.join(publicDir, "plants", "review-needed.json");

const COMMONS_API = "https://commons.wikimedia.org/w/api.php";
const USER_AGENT = "FlowerProject/1.0 (local educational image catalog builder)";

const args = new Map(
  process.argv.slice(2).map((arg) => {
    const [key, value = "true"] = arg.replace(/^--/, "").split("=");
    return [key, value];
  })
);

const limit = Number(args.get("limit") || 0);
const startClass = args.has("start-class") ? Number(args.get("start-class")) : null;
const force = args.get("force") === "true";
const dryRun = args.get("dry-run") === "true";
const localOnly = args.get("local-only") === "true";
const delayMs = Number(args.get("delay") || 900);

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function slugify(value) {
  return String(value || "flower")
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

function pickExtension(mime, url) {
  const fromUrl = new URL(url).pathname.match(/\.(jpe?g|png|webp)$/i)?.[1];
  if (fromUrl) return fromUrl.toLowerCase().replace("jpeg", "jpg");
  if (mime === "image/png") return "png";
  if (mime === "image/webp") return "webp";
  return "jpg";
}

function metadataValue(extmetadata, key) {
  return extmetadata?.[key]?.value || "";
}

function stripHtml(value) {
  return String(value || "").replace(/<[^>]*>/g, "").trim();
}

function buildSearchQueries(plant) {
  const name = plant.name_en;
  return [
    `${name} flower`,
    `${name} plant flower`,
    name,
  ];
}

async function commonsSearch(query) {
  const params = new URLSearchParams({
    action: "query",
    format: "json",
    generator: "search",
    gsrnamespace: "6",
    gsrlimit: "8",
    gsrsearch: query,
    prop: "imageinfo",
    iiprop: "url|mime|size|extmetadata",
    iiurlwidth: "900",
    origin: "*",
  });

  const response = await fetch(`${COMMONS_API}?${params}`, {
    headers: { "User-Agent": USER_AGENT },
  });

  if (!response.ok) {
    throw new Error(`Commons API ${response.status} for query "${query}"`);
  }

  const data = await response.json();
  return Object.values(data.query?.pages || {})
    .map((page) => ({
      pageid: page.pageid,
      title: page.title,
      imageinfo: page.imageinfo?.[0],
    }))
    .filter((item) => item.imageinfo);
}

function scoreCandidate(candidate, plant) {
  const info = candidate.imageinfo;
  const mime = info.mime || "";
  if (!["image/jpeg", "image/png", "image/webp"].includes(mime)) return -1;
  if ((info.width || 0) < 320 || (info.height || 0) < 240) return -1;

  const title = candidate.title.toLowerCase();
  const nameWords = plant.name_en.toLowerCase().split(/\s+/).filter(Boolean);
  let score = 0;

  for (const word of nameWords) {
    if (title.includes(word)) score += 4;
  }
  if (title.includes("flower")) score += 3;
  if (title.includes("rose") && plant.name_en.toLowerCase().includes("rose")) score += 2;
  if (title.includes("diagram") || title.includes("illustration") || title.includes("drawing")) score -= 5;
  if (title.includes("map") || title.includes("logo") || title.includes("icon")) score -= 8;

  const licenseShortName = metadataValue(info.extmetadata, "LicenseShortName");
  if (licenseShortName) score += 1;
  return score;
}

async function findBestImage(plant) {
  const seen = new Set();
  const candidates = [];

  for (const query of buildSearchQueries(plant)) {
    const results = await commonsSearch(query);
    for (const candidate of results) {
      if (seen.has(candidate.pageid)) continue;
      seen.add(candidate.pageid);
      const score = scoreCandidate(candidate, plant);
      if (score >= 0) candidates.push({ ...candidate, score, query });
    }
    if (candidates.some((item) => item.score >= 8)) break;
    await sleep(250);
  }

  candidates.sort((a, b) => b.score - a.score);
  return candidates[0] || null;
}

async function downloadFile(url, destination) {
  const response = await fetch(url, {
    headers: { "User-Agent": USER_AGENT },
  });
  if (!response.ok) throw new Error(`Download ${response.status}: ${url}`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  await writeFile(destination, bytes);
  return bytes.length;
}

async function loadExistingCredits() {
  try {
    const raw = await readFile(creditsPath, "utf8");
    const items = JSON.parse(raw);
    return new Map(items.map((item) => [item.class_id, item]));
  } catch {
    return new Map();
  }
}

function localCreditFor(plant, imageUrl, existingCredit = null) {
  return {
    ...(existingCredit || {}),
    class_id: plant.class_id,
    name_en: plant.name_en,
    display_name: plant.display_name,
    image_url: imageUrl.replaceAll("\\", "/"),
    source: existingCredit?.source || "existing-local-file",
  };
}

function creditFor(plant, candidate, localPath, byteLength) {
  const info = candidate.imageinfo;
  const extmetadata = info.extmetadata || {};
  return {
    class_id: plant.class_id,
    name_en: plant.name_en,
    display_name: plant.display_name,
    image_url: localPath.replaceAll("\\", "/"),
    source: "Wikimedia Commons",
    commons_title: candidate.title,
    commons_page_url: metadataValue(extmetadata, "ImageDescription")
      ? info.descriptionurl
      : `https://commons.wikimedia.org/wiki/${encodeURIComponent(candidate.title.replace(/^File:/, "File:"))}`,
    author: stripHtml(metadataValue(extmetadata, "Artist")) || null,
    license: stripHtml(metadataValue(extmetadata, "LicenseShortName")) || null,
    license_url: metadataValue(extmetadata, "LicenseUrl") || null,
    original_url: info.url,
    downloaded_url: info.thumburl || info.url,
    width: info.thumbwidth || info.width || null,
    height: info.thumbheight || info.height || null,
    bytes: byteLength,
    query: candidate.query,
    score: candidate.score,
  };
}

async function main() {
  const rawCatalog = await readFile(catalogPath, "utf8");
  let plants = JSON.parse(rawCatalog);
  plants = plants.sort((a, b) => a.class_id - b.class_id);

  if (startClass !== null) {
    plants = plants.filter((plant) => plant.class_id >= startClass);
  }
  if (limit > 0) {
    plants = plants.slice(0, limit);
  }

  await mkdir(outputDir, { recursive: true });

  const existingCredits = await loadExistingCredits();
  const credits = [];
  const reviewNeeded = [];

  for (const [index, plant] of plants.entries()) {
    const baseName = `${String(plant.class_id).padStart(3, "0")}-${slugify(plant.name_en)}`;
    const existing = ["jpg", "png", "webp"].find((ext) => existsSync(path.join(outputDir, `${baseName}.${ext}`)));

    if (existing && !force) {
      const imageUrl = `/plants/images/${baseName}.${existing}`;
      credits.push(localCreditFor(plant, imageUrl, existingCredits.get(plant.class_id)));
      console.log(`[${index + 1}/${plants.length}] skip existing ${plant.name_en} -> ${imageUrl}`);
      continue;
    }

    if (localOnly) {
      reviewNeeded.push({
        class_id: plant.class_id,
        name_en: plant.name_en,
        reason: "No local image file found",
      });
      continue;
    }

    try {
      console.log(`[${index + 1}/${plants.length}] search ${plant.class_id}: ${plant.name_en}`);
      const candidate = await findBestImage(plant);

      if (!candidate) {
        reviewNeeded.push({
          class_id: plant.class_id,
          name_en: plant.name_en,
          reason: "No usable Wikimedia Commons image found",
        });
        continue;
      }

      const imageUrl = candidate.imageinfo.thumburl || candidate.imageinfo.url;
      const ext = pickExtension(candidate.imageinfo.mime, imageUrl);
      const fileName = `${baseName}.${ext}`;
      const destination = path.join(outputDir, fileName);
      const localPath = `/plants/images/${fileName}`;

      if (dryRun) {
        credits.push(creditFor(plant, candidate, localPath, 0));
        console.log(`  dry-run ${candidate.title} (${candidate.score})`);
      } else {
        const byteLength = await downloadFile(imageUrl, destination);
        credits.push(creditFor(plant, candidate, localPath, byteLength));
        console.log(`  saved ${localPath} (${byteLength} bytes)`);
      }
    } catch (error) {
      reviewNeeded.push({
        class_id: plant.class_id,
        name_en: plant.name_en,
        reason: error.message,
      });
      console.warn(`  review needed: ${error.message}`);
    }

    await sleep(delayMs);
  }

  await writeFile(creditsPath, `${JSON.stringify(credits, null, 2)}\n`, "utf8");
  await writeFile(reviewPath, `${JSON.stringify(reviewNeeded, null, 2)}\n`, "utf8");

  console.log(`\nDone. Credits: ${creditsPath}`);
  console.log(`Review needed: ${reviewPath}`);
  console.log(`Downloaded or mapped: ${credits.length}`);
  console.log(`Needs review: ${reviewNeeded.length}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
