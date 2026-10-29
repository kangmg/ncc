import { readFileSync } from "node:fs";
import { defineConfig } from "astro/config";

const journal = JSON.parse(readFileSync(new URL("./src/generated/journal.json", import.meta.url), "utf-8"));

export default defineConfig({
  site: journal.site.url,
  base: journal.site.base || "/",
  trailingSlash: "always",
  build: { format: "directory" },
});
