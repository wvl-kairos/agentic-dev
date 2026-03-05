import { useCallback, useEffect, useState } from "react";
import type { RoleTemplate } from "@/types/capability";
import { api } from "@/utils/api";

interface UseRoleTemplatesReturn {
  templates: RoleTemplate[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useRoleTemplates(): UseRoleTemplatesReturn {
  const [templates, setTemplates] = useState<RoleTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(() => {
    setLoading(true);
    setError(null);

    api
      .get<RoleTemplate[]>("/role-templates/")
      .then((data) => setTemplates(data))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { templates, loading, error, refetch: fetch };
}
