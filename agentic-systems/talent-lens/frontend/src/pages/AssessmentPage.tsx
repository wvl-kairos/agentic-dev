import { useParams } from "react-router-dom";
import { useAssessments } from "@/hooks/useAssessments";

export function AssessmentPage() {
  const { id } = useParams<{ id: string }>();
  const { assessments, loading, error } = useAssessments(id!);

  if (loading) return <p>Loading assessment...</p>;
  if (error) return <p className="text-destructive">Error: {error}</p>;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Assessment Scorecard</h2>
      {assessments.length === 0 ? (
        <p className="text-muted-foreground">No assessments found.</p>
      ) : (
        <div className="space-y-6">
          {assessments.map((a) => (
            <div key={a.id} className="rounded-md border p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold capitalize">{a.stage}</h3>
                {a.overall_score != null && (
                  <span className="text-2xl font-bold">
                    {a.overall_score.toFixed(1)}/5.0
                  </span>
                )}
              </div>
              {a.summary && (
                <p className="text-muted-foreground mb-4">{a.summary}</p>
              )}
              {a.criterion_scores.map((cs) => (
                <div key={cs.criterion_name} className="mb-3">
                  <div className="flex justify-between text-sm">
                    <span>{cs.criterion_name}</span>
                    <span>
                      {cs.score}/{cs.max_score}
                    </span>
                  </div>
                  {cs.reasoning && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {cs.reasoning}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
