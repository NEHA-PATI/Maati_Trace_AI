import AppTopbar from "./AppTopbar";

export default function AppShell({ children }) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppTopbar />
      <div className="mx-auto w-full max-w-[1600px] pt-28 md:pt-16">
        <main className="min-h-[calc(100vh-4rem)] w-full">
          {children}
        </main>
      </div>
    </div>
  );
}
