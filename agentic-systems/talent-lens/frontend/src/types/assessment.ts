export interface Evidence {
  quote: string;
  speaker: string | null;
  relevance: string | null;
}

export interface CriterionScore {
  criterion_name: string;
  score: number;
  max_score: number;
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
}
