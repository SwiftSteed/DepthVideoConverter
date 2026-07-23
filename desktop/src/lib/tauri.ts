import { SERVER_BASE } from "./utils";

interface ServerHeartbeat {
  status: "ok" | "error";
  device: string;
  ffmpeg: boolean;
  device_type: string;
  version: string;
}

interface ServerStatus {
  connected: boolean;
  device_type: string;
}

async function getServerHeartbeat(): Promise<ServerHeartbeat> {
  const response = await fetch(`${SERVER_BASE}/api/health`);
  const data = await response.json();
  return {
    status: "ok",
    device_type: data.device_type,
    device: data.device,
    ffmpeg: data.ffmpeg,
    version: data.version,
  };
}

export async function getServerStatus(): Promise<ServerStatus> {
  const heartbeat = await getServerHeartbeat();
  return {
    connected: heartbeat.status === "ok",
    device_type: heartbeat.device_type,
  };
}
