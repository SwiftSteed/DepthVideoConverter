import { create } from "zustand";

interface Settings {
  modelSizeLabel: string;
  resolutionChoice: string;
  invertBW: boolean;
  smoothingStrength: number;
  preserveAudio: boolean;
}

interface SettingsStore extends Settings {
  setModel: (label: string) => void;
  setResolution: (choice: string) => void;
  setInvert: (value: boolean) => void;
  setSmoothing: (value: number) => void;
  setPreserveAudio: (value: boolean) => void;
}

export const useSettingsStore = create<SettingsStore>((set) => ({
  modelSizeLabel: "Small (fastest, ~95 MB)",
  resolutionChoice: "Original",
  invertBW: false,
  smoothingStrength: 60,
  preserveAudio: true,

  setModel: (label) => set({ modelSizeLabel: label }),
  setResolution: (choice) => set({ resolutionChoice: choice }),
  setInvert: (value) => set({ invertBW: value }),
  setSmoothing: (value) => set({ smoothingStrength: value }),
  setPreserveAudio: (value) => set({ preserveAudio: value }),
}));
