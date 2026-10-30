import articlesJson from "../generated/articles.json";
import examplesJson from "../generated/examples.json";
import subjectsJson from "../generated/subjects.json";
import authorsJson from "../generated/authors.json";
import pagesJson from "../generated/pages.json";
import journalJson from "../generated/journal.json";

export interface Author {
  name: string;
  github?: string | null;
  orcid?: string | null;
  corresponding?: boolean | null;
  equal_contribution?: boolean | null;
  affiliations: number[];
}

export interface Translation {
  language: string;
  title: string;
  abstract_html: string;
  body_html: string;
  model: string | null;
  date: string | null;
  machine_translated: boolean;
  disclaimer: string;
  pdf: string | null;
}

export interface AiContribution {
  level: "none" | "assisted" | "substantial" | "agent-led";
  label: string;
  agents: { name: string; model: string | null; provider: string | null; github: string | null; roles: string[] }[];
  oversight: string | null;
  logs: string | null;
}

export interface Version {
  version: number;
  key: string;
  published: string;
  doi: string | null;
  changelog: string | null;
  title: string;
  subtitle: string | null;
  article_type: string;
  type_label: string;
  language: string;
  language_name: string;
  authors: Author[];
  affiliations: string[];
  tags: string[];
  license: string;
  body_kind: "sections" | "markdown" | "typst" | "pdf";
  url: string;
  abstract_html?: string;
  body_html?: string;
  toc_graphic?: string | null;
  cite?: { acs: string; bibtex: string; ris: string };
  supporting_information?: { url: string; file: string; description: string; external: boolean }[];
  mint_doi?: boolean;
  pdf?: string | null;
  bundle?: string | null;
  translation?: Translation | null;
  ai: AiContribution | null;
}

export interface Article {
  id: string;
  example: boolean;
  status: "published" | "withdrawn";
  withdrawn: { date: string; reason: string } | null;
  submitted: string;
  accepted: string;
  issue: number | null;
  concept_doi: string | null;
  year: number;
  volume: number;
  number: string;
  latest: number;
  versions: Version[];
  subjects: string[];
  related: string[];
}

export interface Subject {
  id: string;
  name: string;
  description: string;
  tags: string[];
  articles: string[];
}

export const articles = articlesJson as Article[];
export const examples = examplesJson as Article[];
export const subjects = subjectsJson as Subject[];
export const authors = authorsJson as { github: string; name: string; orcid: string | null; articles: string[] }[];
export const pages = pagesJson as { guide?: string; policy?: string; agents?: string; why?: string; knowledge?: string };
export const journal = journalJson as {
  journal: {
    title: string;
    abbreviation: string;
    short: string;
    tagline: string;
    publisher: string;
    maintainer: { name: string; github: string };
    editor: { name: string };
    founded: number;
    issn: string | null;
  };
  site: { url: string; base: string };
  github: { repo: string; branch: string };
  seed_tags: string[];
  comments: { provider: string | null; giscus: { repo: string; repo_id: string; category: string; category_id: string } };
  doi: { delay_days: number; sandbox: boolean };
  translation: { target: string; model: string };
};

const base = (import.meta.env.BASE_URL || "/").replace(/\/$/, "");

export function u(path: string): string {
  return `${base}${path}`;
}

export function latest(article: Article): Version {
  return article.versions[article.versions.length - 1];
}

export function published(): Article[] {
  return [...articles].sort((a, b) => latest(b).published.localeCompare(latest(a).published) || b.id.localeCompare(a.id));
}

export function byId(id: string): Article | undefined {
  return articles.find((a) => a.id === id);
}

export function slug(tag: string): string {
  return tag.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "tag";
}

export function formatDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00Z`);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
}

export function articlePath(article: Article, version?: number): string {
  if (article.example) return u(`/examples/${article.id.replace(/^example-/, "")}/`);
  return u(`/articles/${version ? `${article.id}v${version}` : article.id}/`);
}

export function citationLine(article: Article): string {
  return `${journal.journal.abbreviation} ${article.year}, ${article.volume}, ${article.number}`;
}

export function subjectById(id: string): Subject | undefined {
  return subjects.find((s) => s.id === id);
}

export function currentVolume(): { number: number; year: number } {
  const year = new Date().getUTCFullYear();
  return { number: year - journal.journal.founded + 1, year };
}

export function issueUrl(template: string): string {
  return `https://github.com/${journal.github.repo}/issues/new?template=${template}`;
}

export const typeOrder = [
  "research-article", "letter", "computational-note", "software", "negative-result", "tutorial", "perspective", "editorial",
];
