export function ProgressBar({ value, label }: { value: number; label: string }) {
  const clamped = Math.min(100, Math.max(0, value))
  return (
    <div
      className="h-2 w-full overflow-hidden rounded-full bg-slate-100"
      role="progressbar"
      aria-label={label}
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className="h-full rounded-full bg-brand-600 transition-[width] duration-500" style={{ width: `${clamped}%` }} />
    </div>
  )
}
