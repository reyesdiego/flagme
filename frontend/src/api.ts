import type { Flag, FlagInput } from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "/api";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "content-type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  listFlags: (): Promise<Flag[]> => http("/flags"),
  createFlag: (input: FlagInput): Promise<Flag> =>
    http("/flags", { method: "POST", body: JSON.stringify(input) }),
  updateFlag: (id: string, input: FlagInput): Promise<Flag> =>
    http(`/flags/${id}`, { method: "PUT", body: JSON.stringify(input) }),
  deleteFlag: (id: string): Promise<void> =>
    http(`/flags/${id}`, { method: "DELETE" }),
};
