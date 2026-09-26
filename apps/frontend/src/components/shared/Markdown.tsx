import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

// LLMs usually write LaTeX with \[ \] and \( \); remark-math only understands $$ and $.
function normalizeMath(text: string) {
  return text
    .replace(/\\\[([\s\S]+?)\\\]/g, (_, expr) => `\n$$\n${expr.trim()}\n$$\n`)
    .replace(/\\\(([\s\S]+?)\\\)/g, (_, expr) => `$${expr.trim()}$`);
}

export function Markdown({ content, className }: { content: string; className?: string }) {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          a: ({ node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" />,
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto">
              <table {...props} />
            </div>
          ),
        }}
      >
        {normalizeMath(content)}
      </ReactMarkdown>
    </div>
  );
}
