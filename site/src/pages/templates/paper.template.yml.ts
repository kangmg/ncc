import type { APIRoute } from "astro";
import { repoFile } from "../../lib/repo";

export const GET: APIRoute = () =>
  new Response(repoFile("templates/paper.template.yml"), { headers: { "Content-Type": "application/yaml; charset=utf-8" } });
