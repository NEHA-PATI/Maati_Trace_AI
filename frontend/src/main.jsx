import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";

import App from "@/app/App";
import { assertFrontendEnvironment } from "@/app/config/environment";
import "@/index.css";

assertFrontendEnvironment();

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

if (!googleClientId) {
  throw new Error("VITE_GOOGLE_CLIENT_ID is not configured.");
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={googleClientId}>
      <App />      
    </GoogleOAuthProvider>
  </React.StrictMode>,
);
