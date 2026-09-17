import type {
  CandidateNode,
  ComparePayload,
  Exclusion,
  Funnel,
  GraphPayload,
  PipelineResult,
  Stage,
  UserSummary,
} from "@/lib/types";

export const MOCK_USERS: UserSummary[] = [
  {
    id: "U-PRIYA",
    name: "Nurse Priya",
    role: "VIEWER",
    department: "ortho",
    ceiling_level: 10,
    write_ceiling: null,
    compliance_clearance: [],
    label: "Nurse Priya — VIEWER, L10, ortho",
  },
  {
    id: "U-VIKRAM",
    name: "Dr. Vikram (HOD)",
    role: "HOD",
    department: "ortho",
    ceiling_level: 4,
    write_ceiling: 4,
    compliance_clearance: ["MNPI"],
    label: "Dr. Vikram — HOD, L4, ortho",
  },
  {
    id: "U-SURESH",
    name: "Admin Suresh",
    role: "ADMIN",
    department: "admin",
    ceiling_level: 1,
    write_ceiling: 1,
    compliance_clearance: ["MNPI", "CONFIDENTIAL", "PHI"],
    label: "Admin Suresh — ADMIN, L1, admin",
  },
];

const MOCK_FUNNEL: Funnel = {
  total_nodes: 50,
  after_bfs: 20,
  after_zone2: 30,
  after_check1: 30,
  after_check2: 25,
  after_check3: 15,
  after_check4: 15,
  after_check5: 13,
  candidate_set: 13,
};

const MOCK_EXCLUSIONS: Exclusion[] = [
  { node_id: "N-O11", title: "Ortho Budget 2026", stage: "compliance", reason: "no clearance for MNPI" },
  { node_id: "N-O12", title: "Ortho Vendor Negotiation", stage: "compliance", reason: "no clearance for CONFIDENTIAL, MNPI" },
];

const MOCK_STAGES: Stage[] = [
  { name: "isolation", label: "Check 1 — ISOLATION", count_in: 30, count_out: 30, removed: 0, duration_ms: 0.003, sql: "AND org_id = 'supra'", excluded: [] },
  { name: "compliance", label: "Check 2 — COMPLIANCE", count_in: 30, count_out: 25, removed: 5, duration_ms: 0.012, sql: "AND NOT (compliance_tags && ARRAY['CONFIDENTIAL', 'MNPI', 'PHI'])", excluded: MOCK_EXCLUSIONS },
  { name: "permission", label: "Check 3 — PERMISSION", count_in: 25, count_out: 15, removed: 10, duration_ms: 0.008, sql: "AND hierarchy_level >= 10 OR zone = 2", excluded: [] },
  { name: "temporal", label: "Check 4 — TEMPORAL", count_in: 15, count_out: 15, removed: 0, duration_ms: 0.002, sql: "AND status = 'ACTIVE' AND (valid_until IS NULL OR valid_until > NOW())", excluded: [] },
  { name: "derivability", label: "Check 5 — DERIVABILITY", count_in: 15, count_out: 13, removed: 2, duration_ms: 0.004, sql: "AND derivability_score < 0.7", excluded: [] },
];

const MOCK_CANDIDATES: CandidateNode[] = [
  {
    id: "N-O14", type: "CONSTRAINT", title: "Patient Rajan: Absolute NSAID Contraindication",
    content: "Patient Rajan has documented allergy to NSAIDs.", importance: 0.99,
    zone: 1, hierarchy_level: 12, hierarchy_level_id: "HL-12-RAJAN",
    department: "ortho", distance_from_entry: 1, compression_hint: "FULL", reached_via: "BFS",
  },
  {
    id: "N-G01", type: "CONSTRAINT", title: "Warfarin-NSAID Interaction",
    content: "Never give NSAIDs to a patient on Warfarin.", importance: 0.98,
    zone: 2, hierarchy_level: 3, hierarchy_level_id: "HL-03-GLOBAL",
    department: null, distance_from_entry: 4, compression_hint: "CONSTRAINT_ONLY", reached_via: "ZONE_2_INJECTION",
  },
  {
    id: "N-015", type: "DECISION", title: "Ortho Night Shift Handover Protocol",
    content: "Night shift handover protocol for orthopaedics.", importance: 0.72,
    zone: 1, hierarchy_level: 10, hierarchy_level_id: "HL-10-ORTHO-W",
    department: "ortho", distance_from_entry: 0, compression_hint: "FULL", reached_via: "BFS",
  },
  {
    id: "N-G05", type: "ANTI_PATTERN", title: "Verbal Orders Without Documentation",
    content: "Verbal orders without documentation are an anti-pattern.", importance: 0.92,
    zone: 2, hierarchy_level: 3, hierarchy_level_id: "HL-03-GLOBAL",
    department: null, distance_from_entry: 4, compression_hint: "CONSTRAINT_ONLY", reached_via: "ZONE_2_INJECTION",
  },
  {
    id: "N-013", type: "FACT", title: "Patient Rajan: Warfarin History",
    content: "Patient Rajan is on Warfarin.", importance: 0.88,
    zone: 1, hierarchy_level: 12, hierarchy_level_id: "HL-12-RAJAN",
    department: "ortho", distance_from_entry: 1, compression_hint: "FULL", reached_via: "BFS",
  },
];

export const MOCK_PIPELINE_RESULT: PipelineResult = {
  user: "U-PRIYA",
  user_name: "Nurse Priya",
  role: "VIEWER",
  department: "ortho",
  ceiling_level: 10,
  write_ceiling: null,
  org: { id: "supra", name: "Supra Multi-Specialty Hospital", config: { derivability_threshold: 0.7 } },
  entry_point: "HL-10-ORTHO-W",
  entry_point_detail: {
    level_id: "HL-10-ORTHO-W",
    level_name: "Ortho Ward",
    level_number: 10,
    department: "ortho",
    strategy: "department_match",
    department_scope: "ortho",
    reason: "best department match at ceiling L10",
  },
  permissions: {
    role: "VIEWER",
    ceiling_level: 10,
    write_ceiling: null,
    readable_levels: [10, 11, 12],
    writable_levels: [],
    cleared_tags: [],
    scoped_clearance: [],
    blocked_tags: ["MNPI", "CONFIDENTIAL", "PHI"],
    zone2_bypasses_ceiling: true,
  },
  traversal: {
    entry_level_id: "HL-10-ORTHO-W",
    reached_levels: { "HL-10-ORTHO-W": 0, "HL-08-ORTHO-GEN": 1, "HL-05-ORTHO": 2, "HL-03-CLIN": 3, "HL-01": 4 },
    visit_order: ["HL-10-ORTHO-W", "HL-12-RAJAN", "HL-08-ORTHO-GEN", "HL-08-TKR", "HL-08-POST-TKR", "HL-05-ORTHO", "HL-05-SURG", "HL-03-CLIN", "HL-01"],
    reachable_node_count: 20,
    multi_parent_levels: ["HL-08-POST-TKR"],
    revisits_prevented: 8,
    max_distance: 4,
  },
  zone2: { injected: ["N-G01", "N-G02", "N-G03", "N-G04", "N-G05", "N-G06", "N-G07", "N-G08", "N-G09", "N-G10"], already_reachable: [], combined_count: 30 },
  pipeline_timing: {
    permission_compile_ms: 0.032,
    entry_point_ms: 0.014,
    bfs_ms: 0.031,
    zone2_inject_ms: 0.012,
    check1_isolation_ms: 0.003,
    check2_compliance_ms: 0.015,
    check3_permission_ms: 0.011,
    check4_temporal_ms: 0.002,
    check5_derivability_ms: 0.004,
    content_fetch_ms: 0.018,
    assemble_ms: 0.009,
    total_ms: 0.66,
  },
  funnel: MOCK_FUNNEL,
  stages: MOCK_STAGES,
  excluded: MOCK_EXCLUSIONS,
  unreachable_node_ids: ["N-C01", "N-C02"],
  distribution: {
    by_type: { CONSTRAINT: 4, DECISION: 1, ANTI_PATTERN: 1, FACT: 5 },
    by_department: { ortho: 6, null: 7 },
    by_compression_hint: { FULL: 5, COMPRESSED: 2, CONSTRAINT_ONLY: 6 },
  },
  llm_calls: 0,
  policy: { zone2_bypasses_ceiling: true, inherit_dept_path: true, derivability_threshold: 0.7 },
  candidate_set: MOCK_CANDIDATES,
};

export const MOCK_GRAPH: GraphPayload = {
  levels: [
    { id: "HL-01", level_number: 1, level_name: "Supra Hospital", department: null, parent_ids: [], zone: 1 },
    { id: "HL-03-CLIN", level_number: 3, level_name: "Clinical Division", department: null, parent_ids: ["HL-01"], zone: 1 },
    { id: "HL-03-GLOBAL", level_number: 3, level_name: "Global Constraints", department: null, parent_ids: ["HL-01"], zone: 2 },
    { id: "HL-05-ORTHO", level_number: 5, level_name: "Orthopaedics Department", department: "ortho", parent_ids: ["HL-03-CLIN"], zone: 1 },
    { id: "HL-05-SURG", level_number: 5, level_name: "Surgery Department", department: "surgery", parent_ids: ["HL-03-CLIN"], zone: 1 },
    { id: "HL-08-ORTHO-GEN", level_number: 8, level_name: "Ortho General", department: "ortho", parent_ids: ["HL-05-ORTHO"], zone: 1 },
    { id: "HL-10-ORTHO-W", level_number: 10, level_name: "Ortho Ward", department: "ortho", parent_ids: ["HL-08-ORTHO-GEN"], zone: 1 },
    { id: "HL-12-RAJAN", level_number: 12, level_name: "Patient: Rajan", department: "ortho", parent_ids: ["HL-10-ORTHO-W"], zone: 1 },
  ],
  nodes: [
    { id: "N-O14", title: "NSAID Contraindication", type: "CONSTRAINT", hierarchy_level_id: "HL-12-RAJAN", hierarchy_level: 12, department: "ortho", zone: 1, importance: 0.99 },
    { id: "N-G01", title: "Warfarin-NSAID", type: "CONSTRAINT", hierarchy_level_id: "HL-03-GLOBAL", hierarchy_level: 3, department: null, zone: 2, importance: 0.98 },
  ],
  edges: [
    { source_id: "N-O14", target_id: "N-G01", edge_type: "SUPPORTS" },
  ],
};

export const MOCK_COMPARE: ComparePayload = {
  results: [MOCK_PIPELINE_RESULT, { ...MOCK_PIPELINE_RESULT, user: "U-VIKRAM", user_name: "Dr. Vikram (HOD)", role: "HOD", funnel: { ...MOCK_FUNNEL, candidate_set: 22 } }],
  shared_node_ids: ["N-G01", "N-O14"],
  exclusive_node_ids: { "U-PRIYA": [], "U-VIKRAM": ["N-O11", "N-O12"] },
};
