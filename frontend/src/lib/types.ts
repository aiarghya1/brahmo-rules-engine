export type NodeType = "CONSTRAINT" | "DECISION" | "ANTI_PATTERN" | "FACT";
export type CompressionHint = "FULL" | "COMPRESSED" | "CONSTRAINT_ONLY";

export interface UserSummary {
  id: string;
  name: string;
  role: string;
  department: string;
  ceiling_level: number;
  write_ceiling: number | null;
  compliance_clearance: string[];
  label: string;
}

export interface CandidateNode {
  id: string;
  type: NodeType;
  title: string;
  content: string;
  importance: number;
  zone: number;
  hierarchy_level: number;
  hierarchy_level_id: string;
  department: string | null;
  distance_from_entry: number;
  compression_hint: CompressionHint;
  reached_via: "BFS" | "ZONE_2_INJECTION";
}

export interface Exclusion {
  node_id: string;
  title: string;
  stage: string;
  reason: string;
}

export interface Stage {
  name: string;
  label: string;
  count_in: number;
  count_out: number;
  removed: number;
  duration_ms: number;
  sql: string;
  excluded: Exclusion[];
}

export interface Funnel {
  total_nodes: number;
  after_bfs: number;
  after_zone2: number;
  after_check1: number;
  after_check2: number;
  after_check3: number;
  after_check4: number;
  after_check5: number;
  candidate_set: number;
}

export interface PipelineResult {
  user: string;
  user_name: string;
  role: string;
  department: string;
  ceiling_level: number;
  write_ceiling: number | null;
  org: { id: string; name: string; config: Record<string, number> };
  entry_point: string;
  entry_point_detail: {
    level_id: string;
    level_name: string;
    level_number: number;
    department: string | null;
    strategy: string;
    department_scope: string | null;
    reason: string;
  };
  permissions: {
    role: string;
    ceiling_level: number;
    write_ceiling: number | null;
    readable_levels: number[];
    writable_levels: number[];
    cleared_tags: string[];
    scoped_clearance: string[];
    blocked_tags: string[];
    zone2_bypasses_ceiling: boolean;
  };
  traversal: {
    entry_level_id: string;
    reached_levels: Record<string, number>;
    visit_order: string[];
    reachable_node_count: number;
    multi_parent_levels: string[];
    revisits_prevented: number;
    max_distance: number;
  };
  zone2: { injected: string[]; already_reachable: string[]; combined_count: number };
  pipeline_timing: Record<string, number>;
  funnel: Funnel;
  stages: Stage[];
  excluded: Exclusion[];
  unreachable_node_ids: string[];
  distribution: {
    by_type: Record<string, number>;
    by_department: Record<string, number>;
    by_compression_hint: Record<string, number>;
  };
  llm_calls: number;
  policy: {
    zone2_bypasses_ceiling: boolean;
    inherit_dept_path: boolean;
    derivability_threshold: number;
  };
  candidate_set: CandidateNode[];
}

export interface HierarchyLevelView {
  id: string;
  level_number: number;
  level_name: string;
  department: string | null;
  parent_ids: string[];
  zone: number;
}

export interface GraphNodeView {
  id: string;
  title: string;
  type: NodeType;
  hierarchy_level_id: string;
  hierarchy_level: number;
  department: string | null;
  zone: number;
  importance: number;
}

export interface GraphPayload {
  levels: HierarchyLevelView[];
  nodes: GraphNodeView[];
  edges: { source_id: string; target_id: string; edge_type: string }[];
}

export interface ComparePayload {
  results: PipelineResult[];
  shared_node_ids: string[];
  exclusive_node_ids: Record<string, string[]>;
}
