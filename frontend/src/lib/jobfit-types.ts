export type JsonRecord = Record<string, unknown>;

export type MatchEvidence = {
  id: string;
  requirement_id?: string | null;
  job_requirement_text: string;
  resume_section_id?: string | null;
  resume_section_type?: string | null;
  resume_evidence_text: string | null;
  match_type: string;
  match_status: string;
  similarity_score?: number | null;
  confidence: number | null;
  explanation: string | null;
  metadata_json?: JsonRecord | null;
  created_at?: string;
};

export type MatchReport = {
  id: string;
  user_id?: string | null;
  session_id?: string | null;
  resume_id: string;
  job_id: string;
  overall_score: number;
  analysis_confidence: number | null;
  breakdown_json: JsonRecord;
  strengths_json: string[] | null;
  gaps_json: string[] | null;
  recommendations_json: string[] | null;
  ats_report_json: JsonRecord | null;
  explanation_json?: JsonRecord | null;
  model_metadata_json?: JsonRecord | null;
  created_at?: string;
  updated_at?: string;
  evidence: MatchEvidence[];
};

export type RewriteSuggestion = {
  id: string;
  optimized_resume_id?: string;
  section_type: string;
  target_location?: string | null;
  original_text: string | null;
  suggested_text: string;
  user_edited_text?: string | null;
  targeted_requirements?: unknown[] | null;
  keywords_added?: unknown[] | null;
  reason: string | null;
  estimated_score_lift: number | null;
  truth_status: string;
  new_claims_json?: unknown[] | null;
  guardrail_reason: string | null;
  decision?: string;
  accepted_by_user?: boolean;
  generated_by_ai_run_id?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type Optimization = {
  id: string;
  user_id?: string | null;
  session_id?: string | null;
  resume_id?: string;
  job_id?: string;
  match_report_id?: string | null;
  version_name?: string;
  content_json?: JsonRecord;
  score_before: number | null;
  score_after: number | null;
  status: string;
  generated_by_ai_run_id?: string | null;
  created_at?: string;
  updated_at?: string;
  suggestions: RewriteSuggestion[];
};

export type ResumeRead = {
  id: string;
  title: string;
  source_type: string;
  original_file_url?: string | null;
  original_file_key?: string | null;
  raw_text: string;
  parse_status?: string;
  parse_confidence: number | null;
  parsed_json?: JsonRecord | null;
  session_id?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type JobRead = {
  id: string;
  title: string | null;
  company: string | null;
  location?: string | null;
  description: string;
  status?: string;
  source_url: string | null;
  work_mode?: string;
  employment_type?: string;
  seniority?: string;
  parse_status?: string;
  parse_confidence: number | null;
  parsed_json?: JsonRecord | null;
  session_id?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type AnalyzeResponse = {
  resume: ResumeRead;
  job: JobRead;
  match_report: MatchReport;
  optimization: Optimization;
};

export type BreakdownRow = {
  label: string;
  value: number;
};
