import { Header } from '@/components/Header';
import { QueryInput } from '@/components/QueryInput';
import { PipelineView } from '@/components/PipelineView';
import { BackgroundGrid } from '@/components/BackgroundGrid';
import { useCruxPipeline } from '@/hooks/useCruxPipeline';

const Index = () => {
  const { state, runPipeline, reset } = useCruxPipeline();

  return (
    <div className="min-h-screen relative">
      <BackgroundGrid />
      
      <div className="container max-w-5xl mx-auto px-4 pb-16">
        <Header />
        
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
    </div>
  );
};

export default Index;
