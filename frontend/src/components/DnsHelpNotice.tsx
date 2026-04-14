interface DnsHelpNoticeProps {
  errorMessage?: string | null;
}

function isLikelyDnsIssue(errorMessage?: string | null): boolean {
  const lower = (errorMessage || "").toLowerCase();
  return (
    lower.includes("failed to fetch") ||
    lower.includes("could not resolve host") ||
    lower.includes("err_name_not_resolved") ||
    lower.includes("dns")
  );
}

export function DnsHelpNotice({ errorMessage }: DnsHelpNoticeProps) {
  if (!isLikelyDnsIssue(errorMessage)) {
    return null;
  }

  return (
    <div className="dns-help-notice" role="status" aria-live="polite">
      <p><strong>Network/DNS issue detected.</strong> If the Railway API domain is not resolving in browser:</p>
      <ol>
        <li>Open <code>brave://settings/security</code> (or browser security settings).</li>
        <li>Enable Secure DNS and select <code>1.1.1.1</code> or <code>8.8.8.8</code>.</li>
        <li>Reload the page and try again.</li>
      </ol>
      <p>
        Refer to: <a href="https://www.loom.com/share/c9bae7f209f84a35925b95d0bb236b57" target="_blank" rel="noreferrer">Loom Demo</a>
      </p>
    </div>
  );
}
