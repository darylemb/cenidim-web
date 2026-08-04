// Minimal zod-based validator mirroring Hoppscotch v2 collection schema
// (packages/hoppscotch-data/src/rest/v/1.ts, collection/v/2.ts).
//
// Usage:
//   node scripts/hoppscotch-validator/validate.mjs scripts/hoppscotch-collection.json
//
// Exits 0 on PASS, 1 on FAIL with a structured error report.
import { z } from "zod";
import fs from "node:fs";
import path from "node:path";

const Param = z.object({
  key: z.string(),
  value: z.string(),
  active: z.boolean(),
  description: z.string().optional(),
});

const Header = z.object({
  key: z.string(),
  value: z.string(),
  active: z.boolean(),
  description: z.string().optional(),
});

const Body = z.union([
  z.object({ contentType: z.null(), body: z.null() }),
  z.object({ contentType: z.literal("multipart/form-data"), body: z.array(z.any()) }),
  z.object({
    contentType: z.enum([
      "application/json", "application/ld+json", "application/hal+json",
      "application/vnd.api+json", "application/xml",
      "application/x-www-form-urlencoded", "text/html", "text/plain",
    ]),
    body: z.string(),
  }),
]);

const Auth = z
  .discriminatedUnion("authType", [
    z.object({ authType: z.literal("none") }),
    z.object({ authType: z.literal("inherit") }),
    z.object({ authType: z.literal("basic"), username: z.string(), password: z.string() }),
    z.object({ authType: z.literal("bearer"), token: z.string() }),
    z.object({
      authType: z.literal("oauth-2"),
      grantTypeInfo: z.any(),
      addTo: z.enum(["HEADERS", "QUERY_PARAMS"]).optional(),
    }),
    z.object({
      authType: z.literal("api-key"),
      key: z.string(),
      value: z.string(),
      addTo: z.string(),
    }),
  ])
  .and(z.object({ authActive: z.boolean() }));

// Accept any v1+ (string) since verzod migrates old requests upward.
const Request = z.object({
  v: z.string().regex(/^\d+$/),
  name: z.string().min(1),
  method: z.string(),
  endpoint: z.string(),
  params: z.array(Param),
  headers: z.array(Header),
  preRequestScript: z.string(),
  testScript: z.string(),
  auth: Auth,
  body: Body,
});

const Collection = z.lazy(() =>
  z.object({
    // HoppCollection.getVersion() reads ``v`` as a number for
    // collections and folders.
    v: z.number().int(),
    name: z.string(),
    requests: z.array(Request),
    folders: z.array(Collection),
    headers: z.array(Header),
    auth: Auth,
  })
);

function count(c) {
  return c.requests.length + c.folders.reduce((s, f) => s + count(f), 0);
}

const file = process.argv[2] ?? path.join(
  path.dirname(new URL(import.meta.url).pathname),
  "..",
  "hoppscotch-collection.json"
);
const data = JSON.parse(fs.readFileSync(file, "utf-8"));
const result = Collection.safeParse(data);

if (result.success) {
  console.log("VALIDATION PASSED");
  console.log(`  file: ${file}`);
  console.log(`  ${data.folders.length} folders, ${count(data)} requests`);
  console.log(`  collection v=${data.v} (number), request v="${data.folders[0]?.requests[0]?.v}" (string)`);
} else {
  console.error("VALIDATION FAILED:");
  console.error(JSON.stringify(result.error.format(), null, 2));
  process.exit(1);
}