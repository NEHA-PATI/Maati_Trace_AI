import { AuthProvider } from "@/features/auth/context/AuthContext";
import SessionInitialiser from "@/features/auth/components/SessionInitialiser";
import { LanguageProvider } from "@/features/language";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Do not hammer the API for deterministic authorization, consent, or
      // routing errors. Retry transient server failures only.
      retry: (failureCount, error) => {
        const status = error?.status;
        if (status >= 400 && status < 500) return false;
        return failureCount < 2;
      },
    },
  },
});

export default function AppProviders({ children }) {
  return <QueryClientProvider client={queryClient}><AuthProvider><LanguageProvider><SessionInitialiser>{children}</SessionInitialiser></LanguageProvider></AuthProvider></QueryClientProvider>;
}
