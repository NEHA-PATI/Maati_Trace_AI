export default function LogoutConfirmModal({ open, loading, onCancel, onConfirm }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-slate-950/40 p-4" role="presentation" onMouseDown={onCancel}>
      <section role="dialog" aria-modal="true" aria-labelledby="logout-confirm-title" className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl" onMouseDown={(event) => event.stopPropagation()}>
        <h2 id="logout-confirm-title" className="text-lg font-black text-slate-950">Log out?</h2>
        <p className="mt-2 text-sm leading-6 text-slate-500">Are you sure you want to end your current session?</p>
        <div className="mt-6 flex justify-end gap-2">
          <button type="button" onClick={onCancel} disabled={loading} className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600 hover:bg-slate-50">Cancel</button>
          <button type="button" onClick={onConfirm} disabled={loading} className="rounded-xl bg-rose-600 px-4 py-2 text-sm font-bold text-white hover:bg-rose-700 disabled:opacity-60">{loading ? "Logging out…" : "Log out"}</button>
        </div>
      </section>
    </div>
  );
}
