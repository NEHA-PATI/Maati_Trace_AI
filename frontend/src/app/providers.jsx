import { AuthProvider } from "@/features/auth/context/AuthContext";
import SessionInitialiser from "@/features/auth/components/SessionInitialiser";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

export default function AppProviders({ children }) {
  return <QueryClientProvider client={queryClient}><AuthProvider><SessionInitialiser>{children}</SessionInitialiser></AuthProvider></QueryClientProvider>;
}
