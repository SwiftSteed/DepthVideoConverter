import { useServerHealth } from "@/hooks/useServerHealth";
import { Activity, Server } from "lucide-react";

export function StatusBar() {
  const { data, isLoading } = useServerHealth();

  const connected = data?.status === "ok";
  const deviceLabel = data?.device ?? "…";
  const ffmpegOk = data?.ffmpeg ?? false;

  return (
    <header className="h-10 px-4 flex items-center gap-4 bg-surface border-b border-custom text-xs select-none shrink-0">
      <div className="flex items-center gap-2">
        <Server className="w-3.5 h-3.5 text-muted" />
        <span className="font-medium">Depth Video Converter</span>
      </div>
      <div className="flex items-center gap-1.5 ml-auto">
        <span
          className={`inline-block w-2 h-2 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`}
        />
        <span className="text-muted">
          {isLoading ? "Connecting…" : connected ? `Server · ${deviceLabel}` : "Disconnected"}
        </span>
        {ffmpegOk && (
          <span className="inline-flex items-center gap-1 text-muted ml-2">
            <Activity className="w-3 h-3" />
            ffmpeg
          </span>
        )}
      </div>
    </header>
  );
}
