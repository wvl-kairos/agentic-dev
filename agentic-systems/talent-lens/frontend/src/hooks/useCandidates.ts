import { useEffect } from "react";
import { useCandidateStore } from "@/stores/candidateStore";

export function useCandidates(ventureId?: string) {
  const { candidates, loading, error, fetchCandidates } = useCandidateStore();

  useEffect(() => {
    fetchCandidates(ventureId);
  }, [fetchCandidates, ventureId]);

  return { candidates, loading, error };
}
