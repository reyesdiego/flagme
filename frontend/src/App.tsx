import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import { FlagForm } from "./FlagForm";
import { FlagsTable } from "./FlagsTable";
import type { Flag, FlagInput } from "./types";

type DialogState =
  | { kind: "closed" }
  | { kind: "new" }
  | { kind: "edit"; flag: Flag };

export default function App() {
  const [flags, setFlags] = useState<Flag[]>([]);
  const [dialog, setDialog] = useState<DialogState>({ kind: "closed" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setFlags(await api.listFlags());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load flags");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return flags;
    return flags.filter(
      (f) =>
        f.key.toLowerCase().includes(q) ||
        (f.environment ?? "").toLowerCase().includes(q) ||
        (f.user_id ?? "").toLowerCase().includes(q),
    );
  }, [flags, query]);

  async function handleSubmit(input: FlagInput) {
    if (dialog.kind === "edit") {
      await api.updateFlag(dialog.flag.id, input);
    } else {
      await api.createFlag(input);
    }
    setDialog({ kind: "closed" });
    await refresh();
  }

  async function handleDelete(flag: Flag) {
    if (!confirm(`Delete flag "${flag.key}"?`)) return;
    try {
      await api.deleteFlag(flag.id);
      await refresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            flagme
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Feature flags, scoped by environment, user, and time.
          </p>
        </div>
        <button
          onClick={() => setDialog({ kind: "new" })}
          className="inline-flex items-center gap-1.5 rounded-md bg-indigo-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          <span aria-hidden>+</span> New flag
        </button>
      </header>

      <div className="mb-4 flex items-center gap-3">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter by key, environment, or user…"
          className="w-full max-w-sm rounded-md border-0 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-indigo-600 dark:bg-slate-900 dark:text-slate-100 dark:ring-slate-700"
        />
        <button
          onClick={() => void refresh()}
          className="rounded-md px-3 py-2 text-sm font-medium text-slate-600 ring-1 ring-slate-300 hover:bg-slate-100 dark:text-slate-300 dark:ring-slate-700 dark:hover:bg-slate-800"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200 dark:bg-red-950/40 dark:text-red-300 dark:ring-red-900">
          {error}
        </div>
      )}

      {loading ? (
        <div className="rounded-xl bg-white p-12 text-center text-slate-500 ring-1 ring-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:ring-slate-800">
          Loading…
        </div>
      ) : (
        <FlagsTable
          flags={filtered}
          onEdit={(flag) => setDialog({ kind: "edit", flag })}
          onDelete={handleDelete}
        />
      )}

      {dialog.kind !== "closed" && (
        <FlagForm
          initial={dialog.kind === "edit" ? dialog.flag : null}
          onCancel={() => setDialog({ kind: "closed" })}
          onSubmit={handleSubmit}
        />
      )}
    </div>
  );
}
