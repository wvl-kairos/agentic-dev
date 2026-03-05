import { useEffect, useState } from "react";
import type { Capability } from "@/types/capability";
import { api } from "@/utils/api";

interface UseCapabilitiesReturn {
  capabilities: Capability[];
  loading: boolean;
  error: string | null;
}

export function useCapabilities(): UseCapabilitiesReturn {
  const [capabilities, setCapabilities] = useState<Capability[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    api
      .get<Capability[]>("/capabilities/")
      .then((data) => setCapabilities(data))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { capabilities, loading, error };
}
