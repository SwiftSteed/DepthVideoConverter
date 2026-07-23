import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { SERVER_BASE } from "@/lib/utils";

interface ProcessParams {
  videoFile: File;
  modelSizeLabel: string;
  resolutionChoice: string;
  invertBW: boolean;
  smoothingStrength: number;
  preserveAudio: boolean;
}

interface ProgressState {
  fraction: number;
  description: string;
}

export function useProcessVideo() {
  const [progress, setProgress] = useState<ProgressState>({
    fraction: 0,
    description: "Ready",
  });
  const [outputBlob, setOutputBlob] = useState<Blob | null>(null);
  const [outputUrl, setOutputUrl] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async (params: ProcessParams) => {
      // Reset state
      setProgress({ fraction: 0, description: "Uploading…" });
      setOutputBlob(null);
      if (outputUrl) URL.revokeObjectURL(outputUrl);
      setOutputUrl(null);

      const formData = new FormData();
      formData.append("input_video", params.videoFile);
      formData.append("model_size_label", params.modelSizeLabel);
      formData.append("resolution_choice", params.resolutionChoice);
      formData.append("invert_bw", String(params.invertBW));
      formData.append("smoothing_strength", String(params.smoothingStrength));
      formData.append("preserve_audio", String(params.preserveAudio));

      setProgress({ fraction: 0.1, description: "Processing…" });

      const res = await fetch(`${SERVER_BASE}/api/process`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Server error: ${res.status}`);
      }

      setProgress({ fraction: 0.95, description: "Downloading result…" });

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);

      setProgress({ fraction: 1.0, description: "Done!" });
      setOutputBlob(blob);
      setOutputUrl(url);

      return { blob, url };
    },
  });

  return {
    ...mutation,
    progress,
    outputBlob,
    outputUrl,
  };
}
