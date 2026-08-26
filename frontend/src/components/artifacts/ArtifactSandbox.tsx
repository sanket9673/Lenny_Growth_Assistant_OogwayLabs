import React, { useMemo } from 'react';
import DOMPurify from 'dompurify';

interface ArtifactSandboxProps {
  content: string;
  type: 'html' | 'svg';
  title: string;
}

export const ArtifactSandbox: React.FC<ArtifactSandboxProps> = ({ content, type, title }) => {
  const sanitizedHtml = useMemo(() => {
    // LAYER 1: DOMPurify Sanitization Engine
    const config: any = {
      ALLOWED_TAGS: [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'b', 'i', 'strong', 'em', 'strike',
        'code', 'pre', 'ul', 'ol', 'li', 'blockquote', 'div', 'span', 'table', 'thead',
        'tbody', 'tr', 'th', 'td', 'img', 'svg', 'path', 'circle', 'rect', 'line', 'polyline',
        'polygon', 'g', 'text', 'tspan', 'defs', 'linearGradient', 'radialGradient', 'stop',
        'style', 'button', 'input', 'label', 'form', 'select', 'option', 'canvas'
      ],
      ALLOWED_ATTR: [
        'href', 'target', 'src', 'alt', 'title', 'class', 'id', 'style', 'width', 'height',
        'viewBox', 'xmlns', 'fill', 'stroke', 'stroke-width', 'stroke-linecap',
        'stroke-linejoin', 'd', 'cx', 'cy', 'r', 'x', 'y', 'x1', 'y1', 'x2', 'y2',
        'points', 'type', 'placeholder', 'value', 'name', 'for'
      ],
      FORBID_TAGS: ['base', 'embed', 'object', 'iframe', 'frame', 'frameset', 'applet', 'script'],
      FORBID_ATTR: ['onload', 'onerror', 'onclick', 'onmouseover', 'onmouseout', 'onkeydown', 'formaction'],
      ALLOW_DATA_ATTR: false,
      ADD_ATTR: ['target'],
    };

    DOMPurify.addHook('afterSanitizeAttributes', (node) => {
      // Force all outer links to open safely in new tab
      if ('target' in node) {
        node.setAttribute('target', '_blank');
        node.setAttribute('rel', 'noopener noreferrer');
      }
      // Neutralize dangerous pseudo-protocols in links
      if (node.hasAttribute('href')) {
        const href = node.getAttribute('href') || '';
        if (href.trim().toLowerCase().startsWith('javascript:')) {
          node.removeAttribute('href');
        }
      }
    });

    const clean = DOMPurify.sanitize(content, config);
    DOMPurify.removeHook('afterSanitizeAttributes');
    return clean;
  }, [content]);

  // LAYER 2: Isolated Origin srcdoc Wrapper + Strict Content Security Policy (CSP)
  const fullDocumentHtml = useMemo(() => {
    if (type === 'svg') {
      return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data: https:;">
  <style>
    body { margin: 0; padding: 16px; display: flex; justify-content: center; align-items: center; background-color: transparent; min-height: 100vh; }
    svg { max-width: 100%; height: auto; }
  </style>
</head>
<body>${sanitizedHtml}</body>
</html>`;
    }

    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' https://cdn.jsdelivr.net; script-src 'unsafe-inline'; img-src data: https:; font-src https:;">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { margin: 0; padding: 16px; font-family: system-ui, -apple-system, sans-serif; background-color: #ffffff; color: #0f172a; }
  </style>
</head>
<body>
  ${sanitizedHtml}
</body>
</html>`;
  }, [sanitizedHtml, type]);

  return (
    <div className="w-full h-full flex flex-col bg-white rounded-b-lg overflow-hidden border border-slate-200">
      {/* 
        CRITICAL SECURITY BOUNDARY:
        sandbox="allow-scripts" WITHOUT allow-same-origin forces the iframe into an opaque unique origin.
        Result: Execution of JS inside cannot access window.parent, cookies, localStorage, or application tokens.
      */}
      <iframe
        title={title}
        srcDoc={fullDocumentHtml}
        sandbox="allow-scripts"
        className="w-full h-full min-h-[500px] border-0 bg-white"
        loading="lazy"
      />
    </div>
  );
};
