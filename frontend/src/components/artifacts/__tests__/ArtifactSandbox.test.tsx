import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ArtifactSandbox } from '../ArtifactSandbox';

describe('ArtifactSandbox Security Test Suite', () => {
  it('neutralizes malicious XSS script tags and onerror vectors', () => {
    const maliciousPayload = `
      <div>
        <h1>Safe Header</h1>
        <script>alert('XSS Attack Execution')</script>
        <img src="invalid.jpg" onerror="alert('DOM XSS Attack')" />
        <a href="javascript:alert('Hijack')">Malicious Link</a>
      </div>
    `;

    const { container } = render(
      <ArtifactSandbox content={maliciousPayload} type="html" title="XSS Test" />
    );

    const iframe = container.querySelector('iframe');
    expect(iframe).not.toBeNull();

    const srcDoc = iframe?.getAttribute('srcdoc') || '';

    // Verify script tag removal
    expect(srcDoc).not.toContain('<script>alert');
    // Verify inline event handler removal
    expect(srcDoc).not.toContain('onerror=');
    // Verify pseudo-protocol removal
    expect(srcDoc).not.toContain('href="javascript:');
    // Verify safe header retention
    expect(srcDoc).toContain('<h1>Safe Header</h1>');
  });

  it('enforces strict iframe sandbox without allow-same-origin', () => {
    const { container } = render(
      <ArtifactSandbox content="<p>Test Content</p>" type="html" title="Sandbox Test" />
    );

    const iframe = container.querySelector('iframe');
    const sandboxAttr = iframe?.getAttribute('sandbox');

    expect(sandboxAttr).toBe('allow-scripts');
    expect(sandboxAttr).not.toContain('allow-same-origin');
  });

  it('injects Content-Security-Policy meta tag inside srcdoc', () => {
    const { container } = render(
      <ArtifactSandbox content="<p>CSP Verification</p>" type="html" title="CSP Test" />
    );

    const iframe = container.querySelector('iframe');
    const srcDoc = iframe?.getAttribute('srcdoc') || '';

    expect(srcDoc).toContain('http-equiv="Content-Security-Policy"');
    expect(srcDoc).toContain("default-src 'none'");
  });
});
