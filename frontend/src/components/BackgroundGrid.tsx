import React from 'react';
import { motion } from 'framer-motion';

export function BackgroundGrid() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      {/* Grid pattern */}
      <div className="absolute inset-0 bg-grid opacity-30" />
      
      {/* Radial gradient overlay */}
      <div 
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse at 50% 0%, hsl(175 84% 46% / 0.08) 0%, transparent 50%)',
        }}
      />
      
      {/* Floating orbs */}
      <motion.div
        className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full"
        style={{
          background: 'radial-gradient(circle, hsl(175 84% 46% / 0.1) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
        animate={{
          x: [0, 50, 0],
          y: [0, 30, 0],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      <motion.div
        className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full"
        style={{
          background: 'radial-gradient(circle, hsl(32 95% 55% / 0.08) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
        animate={{
          x: [0, -40, 0],
          y: [0, -20, 0],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Bottom fade */}
      <div 
        className="absolute bottom-0 left-0 right-0 h-32"
        style={{
          background: 'linear-gradient(to top, hsl(222 47% 6%) 0%, transparent 100%)',
        }}
      />
    </div>
  );
}
