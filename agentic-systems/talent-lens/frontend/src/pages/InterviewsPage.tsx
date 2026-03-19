import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, AlertCircle, ExternalLink, Search, Mic } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/utils/api";
import type { InterviewType } from "@/types/interview";

interface InterviewListItem {
  id: string;
  candidate_id: string | null;
  candidate_name: string | null;
  interview_type: InterviewType;
  source: string | null;
  talk_ratio: number | null;
  duration_seconds: number | null;
  recording_url: string | null;
  created_at: string;
}

const TYPE_LABELS: Record<InterviewType, string> = {
  initial: "Initial",
  screening: "Screening",
  coderpad: "CoderPad",
  technical: "Technical",
  final: "Final",
};

function formatDuration(seconds: number | null): string {
  if (seconds == null) return "--";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

export function InterviewsPage() {
  const navigate = useNavigate();
  const [interviews, setInterviews] = useState<InterviewListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchText, setSearchText] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");

  useEffect(() => {
    setLoading(true);
    api
      .get<InterviewListItem[]>("/interviews/")
      .then(setInterviews)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const sources = useMemo(() => {
    const s = new Set<string>();
    for (const iv of interviews) if (iv.source) s.add(iv.source);
    return Array.from(s).sort();
  }, [interviews]);

  const filtered = useMemo(() => {
    let list = interviews;
    if (typeFilter) list = list.filter((iv) => iv.interview_type === typeFilter);
    if (sourceFilter) list = list.filter((iv) => iv.source === sourceFilter);
    if (searchText) {
      const q = searchText.toLowerCase();
      list = list.filter((iv) =>
        iv.candidate_name?.toLowerCase().includes(q)
      );
    }
    return list;
  }, [interviews, typeFilter, sourceFilter, searchText]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        <span className="ml-2 text-slate-500">Loading interviews...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
        <AlertCircle className="h-5 w-5 text-red-500" />
        <p className="text-sm text-red-700">Failed to load interviews: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Interviews</h2>
        <p className="mt-1 text-sm text-slate-500">
          {filtered.length} of {interviews.length} interview{interviews.length !== 1 && "s"}
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search by candidate..."
            className="w-full rounded-md border border-slate-300 pl-9 pr-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="">All Types</option>
          {(Object.keys(TYPE_LABELS) as InterviewType[]).map((t) => (
            <option key={t} value={t}>{TYPE_LABELS[t]}</option>
          ))}
        </select>
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="">All Sources</option>
          {sources.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-sm text-slate-500">No interviews found.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b bg-slate-50">
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Candidate</th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Type</th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Source</th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Date</th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Duration</th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Talk Ratio</th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Recording</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtered.map((iv) => (
                <tr
                  key={iv.id}
                  onClick={() => {
                    if (iv.candidate_id) navigate(`/assessment/${iv.candidate_id}`);
                  }}
                  className={cn(
                    "transition-colors",
                    iv.candidate_id && "cursor-pointer hover:bg-slate-50"
                  )}
                >
                  <td className="px-4 py-3 text-sm font-medium text-slate-900">
                    {iv.candidate_name ?? <span className="text-slate-400">Unlinked</span>}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">
                    {TYPE_LABELS[iv.interview_type] ?? iv.interview_type}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">
                    {iv.source ?? <span className="text-slate-300">--</span>}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-500">
                    {new Date(iv.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600 tabular-nums">
                    {formatDuration(iv.duration_seconds)}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {iv.talk_ratio != null ? (
                      <span className="inline-flex items-center gap-1 text-slate-600">
                        <Mic className="h-3 w-3" />
                        {Math.round(iv.talk_ratio * 100)}%
                      </span>
                    ) : (
                      <span className="text-slate-300">--</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {iv.recording_url ? (
                      <a
                        href={iv.recording_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                        Link
                      </a>
                    ) : (
                      <span className="text-slate-300">--</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
