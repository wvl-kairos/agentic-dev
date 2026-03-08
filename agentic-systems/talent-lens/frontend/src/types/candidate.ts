export type PipelineStage =
  | "initial_interview"
  | "screening"
  | "coderpad"
  | "technical_interview"
  | "final_interview"
  | "decision"
  | "hired"
  | "rejected";

export interface Candidate {
  id: string;
  venture_id: string;
  name: string;
  email: string | null;
  role: string | null;
  role_template_id: string | null;
  stage: PipelineStage;
  created_at: string;
  updated_at: string;
}
