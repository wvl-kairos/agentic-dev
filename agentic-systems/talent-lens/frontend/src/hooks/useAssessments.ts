import { useEffect, useState } from "react";
import type { Assessment } from "@/types/assessment";
import { api } from "@/utils/api";

export function useAssessments(candidateId: string) {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .get<Assessment[]>(`/assessments/candidate/${candidateId}`)
      .then(setAssessments)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [candidateId]);

  return { assessments, loading, error };
}
