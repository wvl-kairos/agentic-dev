import { useEffect, useMemo, useState } from "react";
import type { Candidate, PipelineStage } from "@/types/candidate";
import { api } from "@/utils/api";

export interface DashboardMetrics {
  totalCandidates: number;
  stageCounts: Record<PipelineStage, number>;
  avgScore: number | null;
}

interface DashboardState {
  candidates: Candidate[];
  metrics: DashboardMetrics;
  loading: boolean;
  error: string | null;
}

const ALL_STAGES: PipelineStage[] = [
  "screening",
  "coderpad",
  "technical_interview",
  "final_interview",
  "decision",
  "hired",
  "rejected",
];

function emptyStageMap(): Record<PipelineStage, number> {
  const map = {} as Record<PipelineStage, number>;
  for (const s of ALL_STAGES) map[s] = 0;
  return map;
}

export function useDashboard(): DashboardState {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [avgScoreFromApi, setAvgScoreFromApi] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    Promise.all([
      api.get<Candidate[]>("/candidates/"),
      api
        .get<{ avg_scores_by_venture: Record<string, number> }>("/dashboard/metrics")
        .catch(() => null),
    ])
      .then(([candidateData, metricsData]) => {
        setCandidates(candidateData);

        // Try to extract a global average from the metrics endpoint
        if (metricsData?.avg_scores_by_venture) {
          const values = Object.values(metricsData.avg_scores_by_venture);
          if (values.length > 0) {
            const sum = values.reduce((a, b) => a + b, 0);
            setAvgScoreFromApi(sum / values.length);
          }
        }
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const metrics = useMemo<DashboardMetrics>(() => {
    const stageCounts = emptyStageMap();
    for (const c of candidates) {
      stageCounts[c.stage] = (stageCounts[c.stage] || 0) + 1;
    }
    return {
      totalCandidates: candidates.length,
      stageCounts,
      avgScore: avgScoreFromApi,
    };
  }, [candidates, avgScoreFromApi]);

  return { candidates, metrics, loading, error };
}
