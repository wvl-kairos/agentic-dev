export interface RubricCriterion {
  id: string;
  name: string;
  description: string | null;
  weight: number;
  max_score: number;
  order: number;
}

export interface Rubric {
  id: string;
  venture_id: string;
  name: string;
  role: string | null;
  description: string | null;
  criteria: RubricCriterion[];
  created_at: string;
}
