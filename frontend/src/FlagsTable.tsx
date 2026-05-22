import type { Flag } from "./types";

type Props = {
  flags: Flag[];
  onEdit: (flag: Flag) => void;
  onDelete: (flag: Flag) => void;
};

function formatScope(value: string | null): React.ReactNode {
  if (value === null) {
    return (
      <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-700">
        all
      </span>
    );
  }
  return <span className="font-mono text-xs">{value}</span>;
}

function formatWindow(starts: string | null, ends: string | null): string {
  if (!starts && !ends) return "always";
  const fmt = (iso: string | null) =>
    iso ? new Date(iso).toLocaleString() : "—";
  return `${fmt(starts)}  →  ${fmt(ends)}`;
}

function formatValue(flag: Flag): React.ReactNode {
  if (flag.value_type === "boolean") {
    const on = flag.boolean_value === true;
    return (
      <span
        className={
          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 " +
          (on
            ? "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-900/40 dark:text-emerald-300 dark:ring-emerald-800"
            : "bg-slate-100 text-slate-600 ring-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-700")
        }
      >
        {on ? "ON" : "OFF"}
      </span>
    );
  }
  return (
    <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-800 dark:bg-slate-800 dark:text-slate-200">
      {flag.string_value}
    </code>
  );
}

export function FlagsTable({ flags, onEdit, onDelete }: Props) {
  if (flags.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
        No flags yet. Click <span className="font-medium">New flag</span> to create one.
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
      <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
        <thead className="bg-slate-50 dark:bg-slate-800/50">
          <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            <th className="px-4 py-3">Key</th>
            <th className="px-4 py-3">Environment</th>
            <th className="px-4 py-3">User</th>
            <th className="px-4 py-3">Active window</th>
            <th className="px-4 py-3">Value</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
          {flags.map((flag) => (
            <tr key={flag.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
              <td className="px-4 py-3">
                <div className="font-medium text-slate-900 dark:text-slate-100">
                  {flag.key}
                </div>
                {flag.description && (
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    {flag.description}
                  </div>
                )}
              </td>
              <td className="px-4 py-3">{formatScope(flag.environment)}</td>
              <td className="px-4 py-3">{formatScope(flag.user_id)}</td>
              <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400">
                {formatWindow(flag.starts_at, flag.ends_at)}
              </td>
              <td className="px-4 py-3">{formatValue(flag)}</td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => onEdit(flag)}
                  className="rounded px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-950/40"
                >
                  Edit
                </button>
                <button
                  onClick={() => onDelete(flag)}
                  className="ml-1 rounded px-2 py-1 text-xs font-medium text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
