import { AppLayout } from "./components/layout/AppLayout";
import { VideoUpload } from "./components/upload/VideoUpload";
import { SettingsPanel } from "./components/settings/SettingsPanel";
import { ProgressPanel } from "./components/progress/ProgressPanel";
import { VideoPreview } from "./components/preview/VideoPreview";

function App() {
  return (
    <AppLayout>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="flex flex-col gap-6">
          <VideoUpload />
          <SettingsPanel />
        </div>
        <div className="flex flex-col gap-6">
          <VideoPreview />
          <ProgressPanel />
        </div>
      </div>
    </AppLayout>
  );
}

export default App;
