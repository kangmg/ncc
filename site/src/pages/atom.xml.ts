import type { APIRoute } from "astro";
import { journal, published, latest, articlePath } from "../lib/data";

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export const GET: APIRoute = ({ site }) => {
  const home = new URL(import.meta.env.BASE_URL.replace(/\/?$/, "/"), site).href;
  const items = published().filter((a) => a.status === "published");
  const updated = items.length ? `${latest(items[0]).published}T00:00:00Z` : new Date().toISOString();
  const entries = items.map((a) => {
    const v = latest(a);
    const url = new URL(articlePath(a), site).href;
    const authors = v.authors
      .map((p) => `<author><name>${esc(p.name)}</name>${p.orcid ? `<uri>https://orcid.org/${p.orcid}</uri>` : ""}</author>`)
      .join("");
    const content = `${v.abstract_html ?? ""}${v.body_html ?? ""}`;
    return `<entry>
<id>${v.doi ? `https://doi.org/${v.doi}` : url}</id>
<title>${esc(v.translation?.title ?? v.title)}</title>
<link rel="alternate" href="${url}"/>
<published>${a.versions[0].published}T00:00:00Z</published>
<updated>${v.published}T00:00:00Z</updated>
${authors}
${v.tags.map((t) => `<category term="${esc(t)}"/>`).join("")}
<rights>${esc(v.license)}</rights>
<summary type="html">${esc(v.abstract_html ?? "")}</summary>
<content type="html">${esc(content)}</content>
</entry>`;
  });
  const body = `<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>${esc(journal.journal.title)}</title>
<subtitle>${esc(journal.journal.tagline)}</subtitle>
<id>${home}</id>
<link rel="alternate" href="${home}"/>
<link rel="self" href="${new URL("atom.xml", home).href}"/>
<updated>${updated}</updated>
<rights>CC BY 4.0 unless stated otherwise</rights>
${entries.join("\n")}
</feed>`;
  return new Response(body, { headers: { "Content-Type": "application/atom+xml; charset=utf-8" } });
};
