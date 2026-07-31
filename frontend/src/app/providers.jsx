import { AuthProvider } from "@/features/auth/context/AuthContext";
import SessionInitialiser from "@/features/auth/components/SessionInitialiser";

export default function AppProviders({ children }) {
  return (
    <AuthProvider>
      <SessionInitialiser>{children}</SessionInitialiser>
    </AuthProvider>
  );
}
