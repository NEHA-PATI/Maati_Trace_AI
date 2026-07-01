import React from "react";
import { Link } from "react-router-dom";

function MaatiLogo() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#f4f0df] shadow-sm ring-1 ring-black/10">
        <svg viewBox="0 0 100 100" className="h-8 w-8">
          <circle cx="50" cy="50" r="48" fill="#f7f3e8" />
          <path d="M28 64 C34 55, 66 55, 72 64 C74 72, 68 80, 58 80 L42 80 C32 80, 26 72, 28 64Z" fill="#7a4b2b" />
          <path d="M34 64 C40 58, 60 58, 66 64" stroke="#c98b56" strokeWidth="5" fill="none" strokeLinecap="round" />
          <path d="M50 60 C50 46, 50 38, 50 28" stroke="#5f7f43" strokeWidth="4" strokeLinecap="round" />
          <path d="M50 38 C39 29, 29 30, 24 22 C34 18, 42 22, 49 33" fill="#a8c76a" opacity="0.95" />
          <path d="M50 38 C61 29, 71 30, 76 22 C66 18, 58 22, 51 33" fill="#a8c76a" opacity="0.95" />
          <circle cx="50" cy="16" r="6" fill="#c99a4a" />
        </svg>
      </div>
      <div className="leading-tight">
        <div className="text-sm font-black tracking-[0.24em]">MAATITRACE</div>
        <div className="text-[10px] uppercase tracking-[0.28em] text-muted-foreground">Field Intelligence Platform</div>
      </div>
    </div>
  );
}

export default function AppTopbar() {
  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b border-border bg-background/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between px-4">
        <Link to="/" aria-label="MaatiTrace home">
          <MaatiLogo />
        </Link>
        <div className="text-xs text-muted-foreground">Gateway-only frontend</div>
      </div>
    </header>
  );
}
