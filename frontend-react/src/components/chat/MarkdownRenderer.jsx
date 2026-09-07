import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

function CodeBlock({ className, children }) {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const lang = match ? match[1] : '';
  const code = String(children).replace(/\n$/, '');

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ position: 'relative', borderRadius: 'var(--radius-md)', overflow: 'hidden', margin: '8px 0' }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '6px 12px', background: '#1a1a2e', fontSize: '0.7rem',
        color: '#8b8b94', fontFamily: 'monospace',
      }}>
        <span>{lang || 'code'}</span>
        <button
          onClick={handleCopy}
          style={{
            display: 'flex', alignItems: 'center', gap: '4px',
            background: 'none', border: 'none', cursor: 'pointer',
            color: copied ? '#22c55e' : '#8b8b94', fontSize: '0.7rem',
          }}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <SyntaxHighlighter
        style={oneDark}
        language={lang || 'text'}
        PreTag="div"
        customStyle={{
          margin: 0,
          padding: '12px 16px',
          fontSize: '0.825rem',
          borderRadius: 0,
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

export default function MarkdownRenderer({ content }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkMath, remarkGfm]}
      rehypePlugins={[rehypeKatex, rehypeRaw]}
      components={{
        code({ node, inline, className, children, ...props }) {
          if (inline) {
            return <code className={className} {...props}>{children}</code>;
          }
          return <CodeBlock className={className}>{children}</CodeBlock>;
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
