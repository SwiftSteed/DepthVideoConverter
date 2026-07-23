import { useProcessVideo } from "@/hooks/useProcessVideo";
import { Loader2 } from "lucide-react";

export function ProgressPanel() {
  const { isPending, progress } = useProcessVideo();

  if (!isPending && progress.fraction === 0) return null;

  const pct = Math.round(progress.fraction * 100);

  return (
    <div className="flex flex-col gap-3 p-4 bg-surface rounded-xl border border-custom">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          {isPending ? "Processing…" : progress.description}
        </span>
        {isPending && <Loader2 className="w-4 h-4 animate-spin text-accent" />}
      </div>

      {/* Progress bar */}
      <div className="w-full h-2 bg-[var(--color-border)] rounded-full overflow-hidden">
        <div
          className="h-full bg-accent rounded-full transition-all duration-300 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>

      <span className="text-xs text-muted">{pct}%</span>
    </div>
  );
}
