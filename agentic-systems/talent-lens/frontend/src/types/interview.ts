export type InterviewType = "initial" | "screening" | "coderpad" | "technical" | "final";

export interface Interview {
  id: string;
  candidate_id: string;
  interview_type: InterviewType;
  source: string | null;
  talk_ratio: number | null;
  duration_seconds: number | null;
  created_at: string;
}
