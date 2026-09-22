import { useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink, Outlet, useNavigate, useParams } from "react-router-dom";
import { REPO_URL, STATIC_DEMO, get, setCurrentUser } from "../lib/api";
import { useCurrentUser } from "../lib/hooks";

const ROLES = [
  { username: "data_scientist", label: "Data scientist" },
  { username: "reviewer", label: "Model risk reviewer" },
  { username: "risk_leader", label: "Risk leader" },
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

export function Layout() {
  const { user, change } = useUser();
  const { id } = useParams();
  const navigate = useNavigate();
  const versions = useQuery({ queryKey: ["versions"], queryFn: () => get("/api/v1/model-versions") });
  const tabs = id
    ? [
        ["", "Version"],
        ["/validation", "Validation"],
        ["/monitoring", "Monitoring"],
        ["/governance", "Governance"],
        ["/executive", "Executive"],
      ]
    : [];
  return (
    <div className="min-h-screen">
      <header className="border-b" style={{ background: "var(--surface-1)", borderColor: "var(--border)" }}>
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 py-3">
          <NavLink to="/" className="text-lg font-bold">
            ModelGuard
          </NavLink>
          <span className="faint hidden text-xs sm:inline">Portfolio simulation · not a lending system</span>
          <nav className="flex flex-wrap items-center gap-1 text-sm">
            <NavLink to="/" end className={({ isActive }) => `rounded px-2 py-1 ${isActive ? "font-semibold" : "muted"}`}>
              Portfolio
            </NavLink>
            {id &&
              tabs.map(([suffix, label]) => (
                <NavLink key={suffix} to={`/versions/${id}${suffix}`} end className={({ isActive }) => `rounded px-2 py-1 ${isActive ? "font-semibold" : "muted"}`}>
                  {label}
                </NavLink>
              ))}
          </nav>
          <div className="ml-auto flex items-center gap-2 text-sm">
            {versions.data && (
              <select className="btn" value={id ?? ""} onChange={(e) => e.target.value && navigate(`/versions/${e.target.value}`)} aria-label="Model version">
                <option value="">Select version…</option>
                {versions.data.map((v: any) => (
                  <option key={v.id} value={v.semantic_version}>
                    {v.semantic_version} · {v.state}
                  </option>
                ))}
              </select>
            )}
            <label className="faint text-xs" htmlFor="role">
              Acting as
            </label>
            <select id="role" className="btn" value={user} onChange={(e) => change(e.target.value)} data-testid="role-switcher">
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
        <div className="border-b px-4 py-2 text-center text-xs" style={{ background: "var(--surface-1)", borderColor: "var(--status-warning)", color: "var(--text-secondary)" }} data-testid="demo-banner">
          <strong style={{ color: "var(--status-warning)" }}>Read-only public demo.</strong> Snapshot of the seeded registry; approvals, alert resolution and free-form copilot questions need the live API —{" "}
          <a className="underline" href={REPO_URL} target="_blank" rel="noreferrer">clone the repo</a> and run <code>make docker-up</code>.
        </div>
      )}
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
      <footer className="faint mx-auto max-w-7xl px-4 pb-8 text-xs">
        ModelGuard is a portfolio project. Metrics come from a synthetic or licensed public dataset; nothing here is credit advice or a compliance claim.
      </footer>
    </div>
  );
}
