import { build } from "esbuild";
import { resolve } from "node:path";

const root = resolve(".");

await build({
  entryPoints: [resolve(root, "src", "app.js")],
  outfile: resolve(root, "static", "app.js"),
  bundle: true,
  format: "iife",
  platform: "browser",
  target: ["chrome109", "safari16"],
});
