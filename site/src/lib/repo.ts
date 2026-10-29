import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export function repoFile(path: string): string {
  return readFileSync(resolve(process.cwd(), "..", path), "utf-8");
}
