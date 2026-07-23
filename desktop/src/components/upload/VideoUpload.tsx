import { useRef, useState } from "react";
import { Upload, Film } from "lucide-react";
import { useProcessVideo } from "@/hooks/useProcessVideo";
import { useSettingsStore } from "@/stores/settingsStore";

export function VideoUpload() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const { mutate: process, isPending } = useProcessVideo();
  const settings = useSettingsStore();

  const handleFile = (f: File | null) => {
    if (!f) return;
    setFile(f);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(f));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f && (f.name.endsWith(".mp4") || f.name.endsWith(".mov"))) {
      handleFile(f);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleProcess = () => {
    if (!file) return;
    process({
      videoFile: file,
      modelSizeLabel: settings.modelSizeLabel,
      resolutionChoice: settings.resolutionChoice,
      invertBW: settings.invertBW,
      smoothingStrength: settings.smoothingStrength,
      preserveAudio: settings.preserveAudio,
    });
  };

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-sm font-semibold text-muted uppercase tracking-wider">
        Input Video
      </h2>

      <input
        ref={fileInputRef}
        type="file"
        accept=".mp4,.mov"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
      />

      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={handleClick}
        className="relative border-2 border-dashed border-custom rounded-xl p-8
                   flex flex-col items-center justify-center gap-3 cursor-pointer
                   hover:border-blue-400 hover:bg-blue-50/50 dark:hover:bg-blue-950/20
                   transition-colors min-h-[200px]"
      >
        {previewUrl ? (
          <video
            src={previewUrl}
            className="max-w-full max-h-[180px] rounded-lg"
            controls
            muted
          />
        ) : (
          <>
            <Upload className="w-10 h-10 text-muted" />
            <div className="text-sm text-center">
              <span className="font-medium text-accent">Click to upload</span>
              <span className="text-muted"> or drag and drop</span>
            </div>
            <p className="text-xs text-muted">MP4 or MOV, any duration</p>
          </>
        )}
      </div>

      {file && (
        <div className="flex items-center gap-2 text-xs text-muted">
          <Film className="w-4 h-4" />
          <span>{file.name}</span>
          <span>·</span>
          <span>{(file.size / 1e6).toFixed(1)} MB</span>
        </div>
      )}

      <button
        onClick={handleProcess}
        disabled={!file || isPending}
        className="w-full py-2.5 rounded-lg font-medium text-sm
                   bg-accent text-white
                   hover:bg-[var(--color-accent-hover)]
                   disabled:opacity-40 disabled:cursor-not-allowed
                   transition-all flex items-center justify-center gap-2"
      >
        {isPending ? "Processing…" : "Process Video"}
      </button>
    </div>
  );
}
