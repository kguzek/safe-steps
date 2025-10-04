"use client";

import React from "react";

export function DotGridBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden bg-white">
      <div className="animate-dotMove absolute inset-0 [background-image:radial-gradient(circle,rgba(0,0,0,0.5)_1px,transparent_1px)] [background-size:28px_28px]" />
      <style jsx global>{`
        @keyframes dotMove {
          0% {
            background-position: 0 0;
          }
          50% {
            background-position: 14px 14px;
          }
          100% {
            background-position: 0 0;
          }
        }
        .animate-dotMove {
          animation: dotMove 6.5s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
