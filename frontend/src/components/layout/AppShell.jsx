import AppTopbar from "./AppTopbar";
import MobileTabBar from "./MobileTabBar";

export default function AppShell({ children }) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <AppTopbar />
      <div className="mx-auto w-full max-w-[1600px] pt-16 md:pt-16">
        <main className="mt-tabbar-safe min-h-[calc(100vh-4rem)] w-full">
          {children}
        </main>
      </div>
      <MobileTabBar />
    </div>
  );
}
