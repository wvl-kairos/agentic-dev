import { useCandidates } from "@/hooks/useCandidates";

export function CandidatesPage() {
  const { candidates, loading, error } = useCandidates();

  if (loading) return <p>Loading candidates...</p>;
  if (error) return <p className="text-destructive">Error: {error}</p>;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Candidates</h2>
      {candidates.length === 0 ? (
        <p className="text-muted-foreground">No candidates yet.</p>
      ) : (
        <div className="space-y-2">
          {candidates.map((c) => (
            <div key={c.id} className="rounded-md border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{c.name}</p>
                  <p className="text-sm text-muted-foreground">{c.role}</p>
                </div>
                <span className="rounded-full bg-secondary px-3 py-1 text-xs">
                  {c.stage}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
