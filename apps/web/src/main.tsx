import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";
import { Layout } from "./components/Layout";
import { Overview } from "./pages/Overview";
import { VersionDetail } from "./pages/VersionDetail";
import { Validation } from "./pages/Validation";
import { Monitoring } from "./pages/Monitoring";
import { Governance } from "./pages/Governance";
import { Executive } from "./pages/Executive";
import { About } from "./pages/About";

// Restore a deep link stashed by public/404.html (GitHub Pages SPA fallback).
try {
  const redirect = sessionStorage.getItem("mg.redirect");
  if (redirect) {
    sessionStorage.removeItem("mg.redirect");
    window.history.replaceState(null, "", redirect);
  }
} catch {
  /* ignore */
}

const client = new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } } });

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={client}>
      <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "")}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Overview />} />
            <Route path="/about" element={<About />} />
            <Route path="/versions/:id" element={<VersionDetail />} />
            <Route path="/versions/:id/validation" element={<Validation />} />
            <Route path="/versions/:id/monitoring" element={<Monitoring />} />
            <Route path="/versions/:id/governance" element={<Governance />} />
            <Route path="/versions/:id/executive" element={<Executive />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
