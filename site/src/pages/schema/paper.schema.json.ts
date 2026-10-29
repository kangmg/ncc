import type { APIRoute } from "astro";
import { repoFile } from "../../lib/repo";

export const GET: APIRoute = () =>
  new Response(repoFile("schema/paper.schema.json"), { headers: { "Content-Type": "application/schema+json; charset=utf-8" } });
