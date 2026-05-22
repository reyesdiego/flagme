import { useEffect, useState } from "react";
import type { Flag, FlagInput, ValueType } from "./types";

type Props = {
  initial?: Flag | null;
  onCancel: () => void;
  onSubmit: (input: FlagInput) => Promise<void>;
};

const blank: FlagInput = {
  key: "",
  description: "",
  environment: null,
  user_id: null,
  starts_at: null,
  ends_at: null,
  value_type: "boolean",
  boolean_value: false,
  string_value: null,
};

// <input type="datetime-local"> wants "YYYY-MM-DDTHH:mm" (no tz).
function toLocalInput(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}`
  );
}

function fromLocalInput(value: string): string | null {
  if (!value) return null;
  return new Date(value).toISOString();
}

export function FlagForm({ initial, onCancel, onSubmit }: Props) {
  const [form, setForm] = useState<FlagInput>(blank);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm(initial ? { ...initial } : blank);
    setError(null);
  }, [initial]);

  const setField = <K extends keyof FlagInput>(key: K, value: FlagInput[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const setValueType = (vt: ValueType) =>
    setForm((prev) => ({
      ...prev,
      value_type: vt,
      boolean_value: vt === "boolean" ? (prev.boolean_value ?? false) : null,
      string_value: vt === "string" ? (prev.string_value ?? "") : null,
    }));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await onSubmit(form);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-slate-900/60 p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-2xl rounded-xl bg-white shadow-2xl ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800"
      >
        <header className="border-b border-slate-200 px-6 py-4 dark:border-slate-800">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {initial ? "Edit flag" : "New flag"}
          </h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Leave environment or user blank to apply globally. Leave start/end blank for an open window.
          </p>
        </header>

        <div className="grid grid-cols-1 gap-4 px-6 py-5 md:grid-cols-2">
          <Field label="Key" required>
            <input
              required
              type="text"
              value={form.key}
              onChange={(e) => setField("key", e.target.value)}
              className={inputClass}
              placeholder="checkout-v2"
            />
          </Field>

          <Field label="Description">
            <input
              type="text"
              value={form.description}
              onChange={(e) => setField("description", e.target.value)}
              className={inputClass}
            />
          </Field>

          <Field label="Environment (blank = all)">
            <input
              type="text"
              value={form.environment ?? ""}
              onChange={(e) =>
                setField("environment", e.target.value.trim() || null)
              }
              className={inputClass}
              placeholder="prod"
            />
          </Field>

          <Field label="User ID (blank = all)">
            <input
              type="text"
              value={form.user_id ?? ""}
              onChange={(e) =>
                setField("user_id", e.target.value.trim() || null)
              }
              className={inputClass}
              placeholder="user_123"
            />
          </Field>

          <Field label="Active from">
            <input
              type="datetime-local"
              value={toLocalInput(form.starts_at)}
              onChange={(e) =>
                setField("starts_at", fromLocalInput(e.target.value))
              }
              className={inputClass}
            />
          </Field>

          <Field label="Active until">
            <input
              type="datetime-local"
              value={toLocalInput(form.ends_at)}
              onChange={(e) =>
                setField("ends_at", fromLocalInput(e.target.value))
              }
              className={inputClass}
            />
          </Field>

          <Field label="Value type">
            <div className="flex gap-2">
              {(["boolean", "string"] as const).map((vt) => (
                <button
                  key={vt}
                  type="button"
                  onClick={() => setValueType(vt)}
                  className={
                    "rounded-md px-3 py-1.5 text-sm font-medium ring-1 transition " +
                    (form.value_type === vt
                      ? "bg-indigo-600 text-white ring-indigo-600"
                      : "bg-white text-slate-700 ring-slate-300 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700 dark:hover:bg-slate-700")
                  }
                >
                  {vt}
                </button>
              ))}
            </div>
          </Field>

          {form.value_type === "boolean" ? (
            <Field label="Boolean value">
              <label className="inline-flex cursor-pointer items-center gap-3 select-none">
                <input
                  type="checkbox"
                  checked={form.boolean_value ?? false}
                  onChange={(e) => setField("boolean_value", e.target.checked)}
                  className="h-5 w-5 rounded border-slate-300 accent-indigo-600"
                />
                <span className="text-sm text-slate-700 dark:text-slate-200">
                  {form.boolean_value ? "Enabled" : "Disabled"}
                </span>
              </label>
            </Field>
          ) : (
            <Field label="String value">
              <input
                type="text"
                required
                value={form.string_value ?? ""}
                onChange={(e) => setField("string_value", e.target.value)}
                className={inputClass}
              />
            </Field>
          )}
        </div>

        {error && (
          <div className="mx-6 mb-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200 dark:bg-red-950/40 dark:text-red-300 dark:ring-red-900">
            {error}
          </div>
        )}

        <footer className="flex items-center justify-end gap-2 border-t border-slate-200 px-6 py-4 dark:border-slate-800">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
          >
            {saving ? "Saving…" : initial ? "Save changes" : "Create flag"}
          </button>
        </footer>
      </form>
    </div>
  );
}

const inputClass =
  "w-full rounded-md border-0 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm ring-1 ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-indigo-600 dark:bg-slate-800 dark:text-slate-100 dark:ring-slate-700";

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      <span className="font-medium text-slate-700 dark:text-slate-300">
        {label}
        {required && <span className="ml-0.5 text-rose-500">*</span>}
      </span>
      {children}
    </label>
  );
}
