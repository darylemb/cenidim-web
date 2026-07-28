// Minimal zod-based validator mirroring Postman v2.1 collection schema
// (https://schema.getpostman.com/json/collection/v2.1.0/collection.json).
//
// Usage:
//   cd backend-fastapi/scripts/postman-validator
//   npm install
//   node validate.mjs ../postman-collection.json
//
// Exits 0 on PASS, 1 on FAIL with a structured error report.
import { z } from "zod";
import fs from "node:fs";
import path from "node:path";

// Recursive Item — either a folder (with nested items) or a request.
const Request = z
  .object({
    name: z.string(),
    request: z.object({
      method: z.string(),
      header: z.array(z.any()).optional(),
      url: z.union([
        z.string(),
        z.object({
          raw: z.string(),
          host: z.array(z.string()).optional(),
          path: z.array(z.string()).optional(),
          variable: z.array(z.any()).optional(),
          query: z.array(z.any()).optional(),
        }),
      ]),
      body: z.any().optional(),
      auth: z.any().optional(),
      description: z.string().optional(),
    }),
    response: z.array(z.any()).optional(),
  })
  .passthrough();

const Item = z.lazy(() =>
  z.union([
    Request,
    z.object({
      name: z.string(),
      item: z.array(Item),
    }).passthrough(),
  ])
);

const Collection = z.object({
  info: z.object({
    _postman_id: z.string(),
    name: z.string(),
    description: z.string().optional(),
    schema: z.string(),
  }),
  item: z.array(Item),
  variable: z.array(z.any()).optional(),
  auth: z.any().optional(),
});

function count(c) {
  return c.item.reduce((s, f) => {
    if (f.item) return s + count(f);
    return s + 1;
  }, 0);
}

const file = process.argv[2] ?? path.join(
  path.dirname(new URL(import.meta.url).pathname),
  "..",
  "postman-collection.json"
);
const data = JSON.parse(fs.readFileSync(file, "utf-8"));
const result = Collection.safeParse(data);

if (result.success) {
  console.log("VALIDATION PASSED");
  console.log(`  file: ${file}`);
  console.log(`  ${data.item.length} folders, ${count(data)} requests`);
  console.log(`  collection: ${data.info.name} (${data.info.schema})`);
  console.log(`  variables: ${(data.variable ?? []).map((v) => `${v.key}=${v.value}`).join(", ")}`);
} else {
  console.error("VALIDATION FAILED:");
  console.error(JSON.stringify(result.error.format(), null, 2));
  process.exit(1);
}