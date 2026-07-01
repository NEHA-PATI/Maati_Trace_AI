import React from "react";
import AppSidebar from "./AppSidebar";
import AppTopbar from "./AppTopbar";

export default function AppShell({ children }) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppTopbar />
      <div className="mx-auto flex w-full max-w-[1600px] pt-16">
        <AppSidebar />
        <main className="min-h-[calc(100vh-4rem)] flex-1 bg-gradient-to-b from-background to-muted/20">
          {children}
        </main>
      </div>
    </div>
  );
}
