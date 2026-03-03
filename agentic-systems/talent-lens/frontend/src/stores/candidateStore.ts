import { create } from "zustand";
import type { Candidate } from "@/types/candidate";
import { api } from "@/utils/api";

interface CandidateStore {
  candidates: Candidate[];
  loading: boolean;
  error: string | null;
  fetchCandidates: (ventureId?: string) => Promise<void>;
}

export const useCandidateStore = create<CandidateStore>((set) => ({
  candidates: [],
  loading: false,
  error: null,
  fetchCandidates: async (ventureId) => {
    set({ loading: true, error: null });
    try {
      const params = ventureId ? `?venture_id=${ventureId}` : "";
      const candidates = await api.get<Candidate[]>(`/candidates/${params}`);
      set({ candidates, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },
}));
