import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

interface Props {
  children: string;
  className?: string;
}

export default function Md({ children, className = "" }: Props) {
  return (
    <div className={`prose-sm max-w-none [&>*:last-child]:mb-0 ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          p: ({ children }) => <p className="mb-1.5 last:mb-0">{children}</p>,
          ul: ({ children }) => <ul className="list-disc pl-4 mb-1.5">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-4 mb-1.5">{children}</ol>,
          li: ({ children }) => <li className="mb-0.5">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
          em: ({ children }) => <em>{children}</em>,
          h1: ({ children }) => <h1 className="text-sm font-bold mb-1">{children}</h1>,
          h2: ({ children }) => <h2 className="text-xs font-bold mb-1">{children}</h2>,
          h3: ({ children }) => <h3 className="text-xs font-semibold mb-0.5">{children}</h3>,
          code: ({ children }) => (
            <code className="bg-s-surface px-1 py-0.5 rounded text-[0.9em] font-mono">{children}</code>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-s-border pl-2 text-s-text-tertiary italic mb-1.5">
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="min-w-full border-collapse border border-s-border text-[10px]">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-s-surface">{children}</thead>,
          tbody: ({ children }) => <tbody>{children}</tbody>,
          tr: ({ children }) => <tr className="border-b border-s-border">{children}</tr>,
          th: ({ children }) => (
            <th className="border border-s-border px-2 py-1.5 text-left font-semibold text-s-text">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-s-border px-2 py-1.5 text-s-text-secondary">
              {children}
            </td>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
