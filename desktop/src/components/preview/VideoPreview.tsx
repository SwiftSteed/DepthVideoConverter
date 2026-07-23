import { useProcessVideo } from "@/hooks/useProcessVideo";
import { Download, Film } from "lucide-react";

export function VideoPreview() {
  const { outputUrl, outputBlob } = useProcessVideo();

  const handleSave = async () => {
    if (!outputBlob) return;

    // Try using the Web Share / download API
    const url = URL.createObjectURL(outputBlob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "depth_output.mp4";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!outputUrl) {
    return (
      <div className="flex flex-col gap-4">
        <h2 className="text-sm font-semibold text-muted uppercase tracking-wider">
          Output
        </h2>
        <div className="flex flex-col items-center justify-center gap-3
                        border-2 border-dashed border-custom rounded-xl p-8 min-h-[200px]">
          <Film className="w-10 h-10 text-muted" />
          <p className="text-sm text-muted text-center">
            Your depth-map video will appear here
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-sm font-semibold text-muted uppercase tracking-wider">
        Output
      </h2>

      <video
        src={outputUrl}
        className="w-full rounded-xl border border-custom"
        controls
        autoPlay
        loop
        muted
      />

      <button
        onClick={handleSave}
        className="flex items-center justify-center gap-2 py-2.5 rounded-lg
                   bg-surface border border-custom text-sm font-medium
                   hover:bg-[var(--color-border)] transition-colors"
      >
        <Download className="w-4 h-4" />
        Save Video
      </button>
    </div>
  );
}
