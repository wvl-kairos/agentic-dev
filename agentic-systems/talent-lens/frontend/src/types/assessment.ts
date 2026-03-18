export type ConfidenceLevel = "demonstrated" | "mentioned" | "claimed";
export type AssessmentStatus = "assessed_positive" | "assessed_negative" | "not_assessed";

export interface Evidence {
  quote: string;
  speaker: string | null;
  relevance: string | null;
}

export interface CriterionScore {
  criterion_name: string;
  score: number;
  max_score: number;
  confidence_level?: ConfidenceLevel;
  assessment_status?: AssessmentStatus;
  reasoning: string | null;
  evidence: Evidence[];
}

export interface Assessment {
  id: string;
  candidate_id: string;
  interview_id: string | null;
  stage: string;
  overall_score: number | null;
  summary: string | null;
  recommendation: string | null;
  criterion_scores: CriterionScore[];
  created_at: string;
  /** Populated client-side by joining interview data. */
  talk_ratio?: number | null;
  /** Populated client-side by joining interview data. */
  recording_url?: string | null;
}

export interface CoverageCriterion {
  criterion_name: string;
  status: AssessmentStatus;
  best_score: number | null;
  max_score: number;
  confidence_level: ConfidenceLevel | null;
  stages: string[];
}

export interface CoverageReport {
  assessed_count: number;
  total_required: number;
  coverage_ratio: number;
  criteria: CoverageCriterion[];
}
