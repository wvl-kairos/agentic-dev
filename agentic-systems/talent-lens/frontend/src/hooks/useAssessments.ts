import { useCallback, useEffect, useState } from "react";
import type { Assessment } from "@/types/assessment";
import type { Candidate } from "@/types/candidate";
import type { Interview } from "@/types/interview";
import { api } from "@/utils/api";

interface UseAssessmentsReturn {
  assessments: Assessment[];
  candidate: Candidate | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useAssessments(candidateId: string): UseAssessmentsReturn {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(() => {
    setLoading(true);
    setError(null);

    Promise.all([
      api.get<Assessment[]>(`/assessments/candidate/${candidateId}`),
      api.get<Candidate>(`/candidates/${candidateId}`),
      api.get<Interview[]>(`/interviews/candidate/${candidateId}`).catch(() => [] as Interview[]),
    ])
      .then(([assessmentData, candidateData, interviews]) => {
        // Build lookups of interview_id -> talk_ratio / recording_url
        const ratioMap = new Map<string, number | null>();
        const recordingMap = new Map<string, string | null>();
        for (const iv of interviews) {
          ratioMap.set(iv.id, iv.talk_ratio);
          recordingMap.set(iv.id, iv.recording_url);
        }

        // Enrich assessments with talk_ratio and recording_url from their linked interview
        const enriched = assessmentData.map((a) => ({
          ...a,
          talk_ratio:
            a.interview_id && ratioMap.has(a.interview_id)
              ? ratioMap.get(a.interview_id) ?? null
              : null,
          recording_url:
            a.interview_id && recordingMap.has(a.interview_id)
              ? recordingMap.get(a.interview_id) ?? null
              : null,
        }));

        setAssessments(enriched);
        setCandidate(candidateData);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [candidateId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { assessments, candidate, loading, error, refetch: fetchData };
}
