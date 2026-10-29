import type { APIRoute } from "astro";
import { repoFile } from "../lib/repo";
import { journal } from "../lib/data";

export const GET: APIRoute = () =>
  new Response(`# Guide for AI agents: ${journal.journal.title}\n\n${repoFile("AGENT_GUIDE.md")}`, {
    headers: { "Content-Type": "text/markdown; charset=utf-8" },
  });
