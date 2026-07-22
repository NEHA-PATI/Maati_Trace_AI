import React from "react";
import { Link } from "react-router-dom";

function MaatiLogo() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#f4f0df] shadow-sm ring-1 ring-black/10">
        <img src="/MaatiAI.png" alt="MaatiTrace logo" className="h-8 w-8 object-contain" />
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
