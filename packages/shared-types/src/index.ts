export type ChallengeTag = "ps" | "img" | "video";

export interface FeatureFlags {
  llm: boolean;
  payments: boolean;
  email: boolean;
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
  code: string;
  request_id?: string | null;
  errors?: Array<Record<string, unknown>>;
}
