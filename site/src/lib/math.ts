import katex from "katex";

const MATH_SPAN = /<span class="math (inline|display)">([\s\S]*?)<\/span>/g;
const ENTITIES: Record<string, string> = { "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'" };

function decode(text: string): string {
  return text.replace(/&(amp|lt|gt|quot|#39);/g, (m) => ENTITIES[m] ?? m);
}

export function renderMath(html: string | undefined | null): string {
  if (!html) return "";
  return html.replace(MATH_SPAN, (_, mode: string, tex: string) =>
    katex.renderToString(decode(tex), { displayMode: mode === "display", throwOnError: false, output: "htmlAndMathml" }),
  );
}
