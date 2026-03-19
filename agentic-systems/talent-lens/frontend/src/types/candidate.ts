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
  salary_expected: number | null;
  orientation: string | null;
  recruiter_name: string | null;
  cv_url: string | null;
  stage: PipelineStage;
  created_at: string;
  updated_at: string;
  /** Populated from linked role template (not stored on candidate). */
  role_salary_min: number | null;
  role_salary_max: number | null;
  role_salary_currency: string | null;
}
