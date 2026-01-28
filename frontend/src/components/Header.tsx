import React from 'react';
import { motion } from 'framer-motion';
import { Brain, Zap, GitBranch, Shield } from 'lucide-react';

export function Header() {
  return (
    <header className="relative z-10 pt-8 pb-12">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-4">
          <motion.div
            className="w-12 h-12 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center glow-primary"
            animate={{ 
              boxShadow: [
                '0 0 20px hsl(175 84% 46% / 0.3)',
                '0 0 40px hsl(175 84% 46% / 0.5)',
                '0 0 20px hsl(175 84% 46% / 0.3)',
              ]
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <Brain className="w-6 h-6 text-primary" />
          </motion.div>
          <div className="text-left">
            <h1 className="text-3xl font-bold tracking-tight">
              <span className="text-gradient">Crux</span>
              <span className="text-foreground ml-2">知几</span>
            </h1>
            <p className="text-xs text-muted-foreground font-mono">
              AgenticRAG Deep Reasoning System
            </p>
          </div>
        </div>

        {/* Tagline */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-muted-foreground max-w-xl mx-auto"
        >
          从浅层搜索到深度推理 —— 基于意图感知的智能研究助手
        </motion.p>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="flex items-center justify-center gap-6 mt-6 text-xs text-muted-foreground"
        >
          <div className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-stage-understand" />
            <span>Schema感知</span>
          </div>
          <div className="flex items-center gap-1.5">
            <GitBranch className="w-3.5 h-3.5 text-stage-retrieve" />
            <span>混合召回</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-stage-judge" />
            <span>深度研判</span>
          </div>
        </motion.div>
      </motion.div>
    </header>
  );
}
