interface ProgressBarProps {
  value: number;
}

export function ProgressBar({ value }: ProgressBarProps) {
  const safe = Math.max(0, Math.min(100, value));

  return (
    <div className="progress-shell">
      <div className="progress-fill" style={{ width: `${safe}%` }} />
      <span className="progress-label">{safe}%</span>
    </div>
  );
}
