import { useQuery } from "@tanstack/react-query";
import { SERVER_BASE } from "@/lib/api";

const POLL_INTERVAL = 30_000;

interface HealthResponse {
  status: string;
  version: string;
  device: string;
  device_type: string;
  ffmpeg: boolean;
}

export function useServerHealth() {
  return useQuery<HealthResponse>({
    queryKey: ["server-health"],
    queryFn: async () => {
      const res = await fetch(`${SERVER_BASE}/api/health`);
      if (!res.ok) throw new Error("Server unreachable");
      return res.json();
    },
    refetchInterval: POLL_INTERVAL,
    retry: true,
    retryDelay: (attempt: number) => Math.min(1000 * 2 ** attempt, 10000),
  });
}
