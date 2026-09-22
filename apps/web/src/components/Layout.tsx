import { useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink, Outlet, useNavigate, useParams } from "react-router-dom";
import { REPO_URL, STATIC_DEMO, get, setCurrentUser } from "../lib/api";
import { useCurrentUser } from "../lib/hooks";
import { STATE_LABEL } from "../lib/glossary";

const ROLES = [
  { username: "risk_leader", label: "Risk leader" },
  { username: "reviewer", label: "Model risk reviewer" },
  { username: "data_scientist", label: "Data scientist" },
];

export function useUser() {
  const user = useCurrentUser();
  const qc = useQueryClient();
  const change = (u: string) => {
    setCurrentUser(u);
    qc.invalidateQueries();
  };
  return { user, change };
}

const TABS: [string, string][] = [
  ["/executive", "Summary"],
  ["", "Details"],
  ["/validation", "Model quality"],
  ["/monitoring", "Monitoring"],
  ["/governance", "Approval"],
];

export function Layout() {
  const { user, change } = useUser();
  const { id } = useParams();
  const navigate = useNavigate();
  const versions = useQuery({ queryKey: ["versions"], queryFn: () => get("/api/v1/model-versions") });
  const link = ({ isActive }: { isActive: boolean }) =>
    `rounded-md px-2.5 py-1 text-sm transition-colors ${isActive ? "font-semibold" : "muted hover:text-[var(--text)]"}`;
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b backdrop-blur" style={{ background: "color-mix(in srgb, var(--surface) 88%, transparent)", borderColor: "var(--hairline)" }}>
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <NavLink to="/" className="text-[17px] font-semibold tracking-tight">
            ModelGuard
          </NavLink>
          <nav className="flex flex-wrap items-center gap-1" aria-label="Main">
            <NavLink to="/" end className={link}>
              All models
            </NavLink>
            {id && <span className="faint px-1" aria-hidden>/</span>}
            {id && TABS.map(([suffix, label]) => (
              <NavLink key={suffix} to={`/versions/${id}${suffix}`} end className={link}>
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2 text-sm">
            {versions.data && (
              <select className="field w-auto" value={id ?? ""} onChange={(e) => e.target.value && navigate(`/versions/${e.target.value}/executive`)} aria-label="Model version">
                <option value="">Choose a model…</option>
                {versions.data.map((v: any) => (
                  <option key={v.id} value={v.semantic_version}>
                    {v.semantic_version} · {STATE_LABEL[v.state] ?? v.state}
                  </option>
                ))}
              </select>
            )}
            <label className="faint whitespace-nowrap text-xs" htmlFor="role">
              View as
            </label>
            <select id="role" className="field w-auto" value={user} onChange={(e) => change(e.target.value)} data-testid="role-switcher">
              {ROLES.map((r) => (
                <option key={r.username} value={r.username}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>
      {STATIC_DEMO && (
        <div className="border-b px-4 py-2 text-center text-[13px]" style={{ background: "var(--warning-bg)", borderColor: "var(--hairline)", color: "var(--text-2)" }} data-testid="demo-banner">
          This is a read-only demonstration with a fixed snapshot of results. Approving, rejecting and resolving alerts need the full application —{" "}
          <a className="underline" href={REPO_URL} target="_blank" rel="noreferrer">available on GitHub</a>.
        </div>
      )}
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
      <footer className="faint mx-auto max-w-6xl px-4 pb-10 text-[13px]">
        ModelGuard is a portfolio project that simulates how a credit-risk model is built, checked, approved and watched over time. Figures come from a public,
        openly licensed dataset and a synthetic sample; nothing here is credit advice or a compliance claim.
      </footer>
    </div>
  );
}
