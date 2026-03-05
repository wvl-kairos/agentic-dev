export interface CapabilityLevel {
  id: string;
  level: number;
  title: string;
  description: string | null;
}

export interface Technology {
  id: string;
  name: string;
  slug: string;
  icon: string | null;
  capability_id: string;
  order: number;
}

export interface Capability {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  icon: string | null;
  order: number;
  levels: CapabilityLevel[];
  technologies: Technology[];
}

export interface RoleCapabilityRequirement {
  id: string;
  capability_id: string;
  capability: Capability | null;
  required_level: number;
}

export interface RoleTechnologyRequirement {
  id: string;
  technology_id: string;
  technology: Technology | null;
  required_level: number;
}

export interface RoleTemplate {
  id: string;
  venture_id: string;
  name: string;
  description: string | null;
  requirements: RoleCapabilityRequirement[];
  technology_requirements: RoleTechnologyRequirement[];
  created_at: string;
}

export interface CandidateCapabilityScore {
  capability_id: string;
  capability_name: string;
  capability_slug: string;
  required_level: number | null;
  avg_score: number | null;
  max_score: number;
  assessment_count: number;
}

export interface CandidateSkills {
  candidate_id: string;
  candidate_name: string;
  role_template: RoleTemplate | null;
  capabilities: CandidateCapabilityScore[];
}
