import React from "react";
import ReactDOM from "react-dom/client";

import App from "@/app/App";
import { assertFrontendEnvironment } from "@/app/config/environment";
import "@/index.css";

assertFrontendEnvironment();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
