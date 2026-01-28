import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Play, RotateCcw, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface QueryInputProps {
  onSubmit: (query: string) => void;
  onReset: () => void;
  isRunning: boolean;
  isCompleted: boolean;
}

const exampleQueries = [
  'AgenticRAG 如何实现深度推理能力？',
  '对比 ReAct 和 Chain-of-Thought 的技术差异',
  '为什么传统 RAG 无法处理复杂多跳问题？',
  'LLM Agent 的浏览器操作框架设计原理',
];

export function QueryInput({ onSubmit, onReset, isRunning, isCompleted }: QueryInputProps) {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isRunning) {
      onSubmit(query.trim());
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    if (!isRunning) {
      onSubmit(example);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Main input */}
      <form onSubmit={handleSubmit}>
        <motion.div
          className={cn(
            "relative rounded-xl border-2 transition-all duration-300",
            isFocused 
              ? "border-primary glow-primary" 
              : "border-border hover:border-primary/50"
          )}
          animate={{
            scale: isFocused ? 1.01 : 1,
          }}
          transition={{ duration: 0.2 }}
        >
          <div className="flex items-center p-2">
            <Search className={cn(
              "w-5 h-5 mx-3 transition-colors",
              isFocused ? "text-primary" : "text-muted-foreground"
            )} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="输入您的研究问题..."
              disabled={isRunning}
              className={cn(
                "flex-1 bg-transparent border-none outline-none text-lg",
                "placeholder:text-muted-foreground/50",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            />
            
            {isCompleted ? (
              <Button
                type="button"
                onClick={onReset}
                variant="outline"
                size="sm"
                className="mr-2"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                重新开始
              </Button>
            ) : (
              <Button
                type="submit"
                disabled={!query.trim() || isRunning}
                size="sm"
                className="mr-2 bg-primary hover:bg-primary/90"
              >
                {isRunning ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    >
                      <Sparkles className="w-4 h-4 mr-2" />
                    </motion.div>
                    分析中...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    开始分析
                  </>
                )}
              </Button>
            )}
          </div>
        </motion.div>
      </form>

      {/* Example queries */}
      {!isRunning && !isCompleted && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mt-4"
        >
          <div className="text-xs text-muted-foreground mb-2">示例查询：</div>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.map((example, i) => (
              <button
                key={i}
                onClick={() => handleExampleClick(example)}
                className={cn(
                  "px-3 py-1.5 text-xs rounded-full border border-border",
                  "bg-muted/30 hover:bg-muted/50 hover:border-primary/50",
                  "transition-all duration-200 text-left"
                )}
              >
                {example}
              </button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
