import { useAuth } from "@/features/auth/context/useAuth";

export default function SessionInitialiser({ children }) {
  const { initialising } = useAuth();
  if (initialising) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50">
        <div className="text-center">
          <span className="mx-auto block h-8 w-8 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-700" />
          <p className="mt-3 text-sm text-slate-600">Restoring your secure session…</p>
        </div>
      </div>
    );
  }
  return children;
}
