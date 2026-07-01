import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { API_BASE_URL } from "@/lib/api/client";
import { getFpos } from "@/lib/api/fpo";
import { Button } from "@/components/ui/button";

export default function AdminDashboard() {
  const [routes, setRoutes] = useState([]);
  const [fpos, setFpos] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      fetch(`${API_BASE_URL}/api/routes`).then((r) => r.json()).catch(() => ({ routes: [] })),
      getFpos().catch(() => []),
    ]).then(([routeData, fpoData]) => {
      if (!active) return;
      setRoutes(routeData.routes || Object.entries(routeData || {}).map(([key, value]) => ({ prefix: key, target: value })));
      setFpos(Array.isArray(fpoData) ? fpoData : []);
    }).catch((err) => {
      if (!active) return;
      setError(err.message || "Failed to load admin dashboard");
    });
    return () => { active = false; };
  }, []);

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div>
        <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Gateway Admin</div>
        <h1 className="text-3xl font-black">Launch command center</h1>
        <p className="text-sm text-muted-foreground">Frontend is reading gateway routes and live farm registry data through `http://localhost:8000` only.</p>
      </div>
      {error ? <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div> : null}
      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <Stat label="FPOs" value={fpos.length} />
        <Stat label="Farmers" value="endpoint pending" />
        <Stat label="Farms" value="endpoint pending" />
        <Stat label="Acres" value="endpoint pending" />
        <Stat label="H3 records" value="endpoint pending" />
        <Stat label="Grid records" value="endpoint pending" />
      </div>
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-3xl border bg-card p-5">
          <div className="mb-4 text-lg font-bold">Gateway route inventory</div>
          <div className="space-y-3">
            {routes.length ? routes.map((route) => (
              <div key={`${route.prefix}-${route.target}`} className="flex items-center justify-between rounded-2xl border p-3 text-sm">
                <div className="font-semibold">/api/{route.prefix}</div>
                <div className="text-muted-foreground">{route.target}</div>
              </div>
            )) : <div className="text-sm text-muted-foreground">No route list returned.</div>}
          </div>
        </section>
        <section className="rounded-3xl border bg-card p-5">
          <div className="mb-4 flex items-center justify-between">
            <div className="text-lg font-bold">FPO workspaces</div>
            <Button asChild size="sm"><Link to="/my-fpo">Open My FPO</Link></Button>
          </div>
          <div className="space-y-3">
            {fpos.length ? fpos.map((fpo) => (
              <Link key={fpo.fpo_id} to={`/fpo/${fpo.fpo_id}`} className="block rounded-2xl border p-4 transition hover:border-primary/40 hover:bg-muted/30">
                <div className="font-semibold">{fpo.fpo_name}</div>
                <div className="text-sm text-muted-foreground">{fpo.district_name}, {fpo.state_name}</div>
              </Link>
            )) : <div className="text-sm text-muted-foreground">No FPO rows available yet.</div>}
          </div>
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-3xl border bg-card p-4">
      <div className="text-xs uppercase tracking-[0.24em] text-muted-foreground">{label}</div>
      <div className="mt-2 text-2xl font-black">{value}</div>
    </div>
  );
}
