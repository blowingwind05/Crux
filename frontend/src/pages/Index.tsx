import { useState } from 'react';
import { Header } from '@/components/Header';
import { QueryInput } from '@/components/QueryInput';
import { PipelineView } from '@/components/PipelineView';
import { BackgroundGrid } from '@/components/BackgroundGrid';
import { SettingsPanel } from '@/components/SettingsPanel';
import { useCruxPipeline } from '@/hooks/useCruxPipeline';

const Index = () => {
  const { state, runPipeline, reset } = useCruxPipeline();
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="min-h-screen relative">
      <BackgroundGrid />

      <div className="container max-w-[1400px] mx-auto px-4 pb-16">
        <Header onSettingsClick={() => setShowSettings(true)} />

        <main>
          <QueryInput
            onSubmit={runPipeline}
            onReset={reset}
            isRunning={state.isRunning}
            isCompleted={state.isCompleted}
          />

          <PipelineView state={state} />
        </main>
      </div>

      <SettingsPanel
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </div>
  );
};

export default Index;
