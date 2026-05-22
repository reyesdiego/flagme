export type ValueType = "boolean" | "string";

export interface Flag {
  id: string;
  key: string;
  description: string;
  environment: string | null;
  user_id: string | null;
  starts_at: string | null;
  ends_at: string | null;
  value_type: ValueType;
  boolean_value: boolean | null;
  string_value: string | null;
}

export type FlagInput = Omit<Flag, "id">;
