Everything this journal publishes is open knowledge. Besides the article pages and PDFs, every published version is
available as structured data and as plain Markdown, and an MCP server lets AI agents search and read the journal
directly. Think of it as a wiki whose entries are citable, versioned articles: each entry has a stable ID, a version
history, a DOI, a licence, subjects and keywords that link it to related entries, and a statement of how it was
screened. The rules for using it are in the [editorial policy](https://kangmg.github.io/journal/policy/#knowledge-base).

## Endpoints

All endpoints are static files: no account, no key, no rate limit beyond the hosting provider's.

| Resource | Address |
|---|---|
| Index of articles and subjects (JSON) | [`/api/v1/index.json`](https://kangmg.github.io/journal/api/v1/index.json) |
| One article, latest version (JSON) | `/api/v1/articles/<id>.json`, e.g. [`2026-0001.json`](https://kangmg.github.io/journal/api/v1/articles/2026-0001.json) |
| One article, specific version (JSON) | `/api/v1/articles/<id>v<n>.json` |
| One article as Markdown with YAML front matter | `/articles/<id>.md` or `/articles/<id>v<n>.md` |
| Full text of all published articles | [`/llms-full.txt`](https://kangmg.github.io/journal/llms-full.txt) |
| Short index for language models | [`/llms.txt`](https://kangmg.github.io/journal/llms.txt) |
| Feed of new articles with full text | [`/atom.xml`](https://kangmg.github.io/journal/atom.xml) |

An article record contains the metadata (title, authors, affiliations, subjects, keywords, dates, DOI, licence), the
abstract, the full text in Markdown (or the extracted text of a PDF submission), references, data and code
availability, the AI disclosure, citations in ACS, BibTeX, and RIS, the version history, and a `review` field that
states how the article was checked. Non-English articles also carry the English machine translation, marked as such.
Withdrawn articles keep only their metadata and the withdrawal notice.

## MCP server

The MCP server runs on your machine and reads the public endpoints above. It needs
[uv](https://docs.astral.sh/uv/).

Claude Code:

```bash
claude mcp add ncc -- uvx --from "jtools[mcp] @ git+https://github.com/kangmg/journal" ncc-mcp
```

Claude Desktop, Cursor, and other clients that use a JSON configuration:

```json
{
  "mcpServers": {
    "ncc": {
      "command": "uvx",
      "args": ["--from", "jtools[mcp] @ git+https://github.com/kangmg/journal", "ncc-mcp"]
    }
  }
}
```

| Tool | What it returns |
|---|---|
| `search_articles(query, subject?, limit?)` | Ranked summaries by title, keywords, subjects, authors, and abstract |
| `get_article(article_id, version?)` | The full record of one article version |
| `list_subjects()` | Subjects with descriptions, keywords, and article IDs |
| `recent_articles(limit?)` | Newest articles first |
| `cite_article(article_id, version?, style?)` | A citation in ACS, BibTeX, or RIS |

The resource `ncc://articles/{article_id}` returns an article as Markdown. Set `NCC_SITE` to point the server at a
mirror or a local build.

## Using the content

- **Licence.** Reuse follows each article's licence, CC BY 4.0 unless the record says otherwise. Attribute the
  authors, the title, the journal, the version, and the DOI or URL. `cite_article` produces this.
- **What an article is.** Articles are shared results, screened for scope and spam, not peer-reviewed. Check the
  `review` field before presenting a result as established. AI translations and AI contributions are labelled in the
  record.
- **Versions.** Cite the version you used. The address without a version always returns the latest one.
- **Stability.** Fields in API version 1 are only added, never removed or renamed. A breaking change would ship as
  `/api/v2/` with notice in the repository.
