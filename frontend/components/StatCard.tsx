import clsx from "clsx";
import { LucideIcon } from "lucide-react";

export default function StatCard({
  label,
  value,
  icon: Icon,
  tone = "default",
  hint,
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  tone?: "default" | "amber" | "steel" | "warn";
  hint?: string;
}) {
  const toneMap: Record<string, string> = {
    default: "text-ink",
    amber: "text-amber",
    steel: "text-steel",
    warn: "text-status-warn",
  };

  return (
    <div className="plate rivet rounded p-5">
      <div className="flex items-start justify-between">
        <div>
          <div className="font-mono text-[10px] tracking-widest text-ink-faint uppercase mb-2">
            {label}
          </div>
          <div className={clsx("font-display text-3xl font-semibold tabular-nums", toneMap[tone])}>
            {value}
          </div>
          {hint && <div className="text-xs text-ink-muted mt-1">{hint}</div>}
        </div>
        <Icon className="w-4 h-4 text-ink-faint" strokeWidth={2} />
      </div>
    </div>
  );
}
