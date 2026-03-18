export type InterviewType = "initial" | "screening" | "coderpad" | "technical" | "final";

export interface Interview {
  id: string;
  candidate_id: string;
  interview_type: InterviewType;
  source: string | null;
  talk_ratio: number | null;
  duration_seconds: number | null;
  recording_url: string | null;
  created_at: string;
}

export interface InterviewDetail extends Interview {
  transcript: string | null;
}
