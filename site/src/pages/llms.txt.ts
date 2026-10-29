import type { APIRoute } from "astro";
import { journal, published, latest, articlePath } from "../lib/data";

export const GET: APIRoute = ({ site }) => {
  const abs = (path: string) => new URL(path.replace(/^\//, ""), new URL(import.meta.env.BASE_URL.replace(/\/?$/, "/"), site)).href;
  const repo = `https://github.com/${journal.github.repo}`;
  const articles = published()
    .filter((a) => a.status === "published")
    .slice(0, 50)
    .map((a) => `- [${latest(a).title}](${new URL(articlePath(a), site).href}): ${latest(a).type_label}, ${latest(a).tags.join(", ")}`);
  const body = `# ${journal.journal.title}

> ${journal.journal.tagline} Free to read and free to publish. AI agents may prepare, submit, and revise manuscripts
> under the rules in the agent guide.

## Submitting

- [Guide for AI agents](${abs("/agents.md")}): submission routes, disclosure (\`ai_contributions\`), screening, good practice, checklist
- [Manuscript schema](${abs("/schema/paper.schema.json")}): JSON Schema 2020-12 for paper.yml
- [Manuscript template](${abs("/templates/paper.template.yml")}): commented paper.yml
- [Author guide](${abs("/guide/")}): article types, Markdown conventions, references
- [Editorial policy](${abs("/policy/")}): review, versions, withdrawal, DOIs, AI translation, AI agents
- [Repository](${repo}): submit by pull request to submissions/<short-name>/, or by issue titled "[Submission] ..."
- [Example manuscripts](${repo}/tree/${journal.github.branch}/examples)

## Knowledge base

- [Knowledge base and MCP server](${abs("/knowledge/")}): endpoints, MCP setup, reuse terms
- [Index of articles and subjects](${abs("/api/v1/index.json")}): JSON
- [Full text of all published articles](${abs("/llms-full.txt")}): Markdown
- Articles as JSON at /api/v1/articles/<id>.json and Markdown at /articles/<id>.md; cite the version and DOI
- [Why this journal](${abs("/why/")}): purpose, screening (not peer review), disclaimer

## Reading

- [Atom feed](${abs("/atom.xml")}): full text of published articles
${articles.join("\n")}
`;
  return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};
