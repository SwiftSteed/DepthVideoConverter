import { useSettingsStore } from "@/stores/settingsStore";
import { Settings2 } from "lucide-react";

export function SettingsPanel() {
  const store = useSettingsStore();

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Settings2 className="w-4 h-4 text-muted" />
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wider">
          Settings
        </h2>
      </div>

      <div className="grid gap-4 p-4 bg-surface rounded-xl border border-custom">
        {/* Model size */}
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted">Model Size</span>
          <select
            className="w-full rounded-lg border border-custom bg-[var(--color-bg)] px-3 py-2 text-sm"
            value={store.modelSizeLabel}
            onChange={(e) => store.setModel(e.target.value)}
          >
            <option>Small (fastest, ~95 MB)</option>
            <option>Base (balanced, ~372 MB)</option>
            <option>Large (best quality, ~1.2 GB)</option>
          </select>
        </label>

        {/* Resolution */}
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted">Output Resolution</span>
          <select
            className="w-full rounded-lg border border-custom bg-[var(--color-bg)] px-3 py-2 text-sm"
            value={store.resolutionChoice}
            onChange={(e) => store.setResolution(e.target.value)}
          >
            <option>Original</option>
            <option>480p (854×480)</option>
            <option>720p (1280×720)</option>
            <option>1080p (1920×1080)</option>
          </select>
        </label>

        {/* Invert B&W */}
        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            className="w-4 h-4 rounded accent-[var(--color-accent)]"
            checked={store.invertBW}
            onChange={(e) => store.setInvert(e.target.checked)}
          />
          <div className="flex flex-col">
            <span className="text-sm font-medium">Invert Black &amp; White</span>
            <span className="text-xs text-muted">Swap near ↔ far</span>
          </div>
        </label>

        {/* Smoothing */}
        <label className="flex flex-col gap-1.5">
          <div className="flex justify-between">
            <span className="text-xs font-medium text-muted">Temporal Smoothing</span>
            <span className="text-xs text-muted">{store.smoothingStrength}%</span>
          </div>
          <input
            type="range"
            min={0}
            max={100}
            value={store.smoothingStrength}
            onChange={(e) => store.setSmoothing(Number(e.target.value))}
            className="w-full accent-[var(--color-accent)]"
          />
        </label>

        {/* Preserve audio */}
        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            className="w-4 h-4 rounded accent-[var(--color-accent)]"
            checked={store.preserveAudio}
            onChange={(e) => store.setPreserveAudio(e.target.checked)}
          />
          <div className="flex flex-col">
            <span className="text-sm font-medium">Preserve Original Audio</span>
            <span className="text-xs text-muted">Copy audio track to output</span>
          </div>
        </label>
      </div>
    </div>
  );
}
