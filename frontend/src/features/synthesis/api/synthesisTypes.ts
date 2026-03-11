/**
 * Types for Reasoning Synthesis Engine (Phase 4E)
 */

export enum SynthesisType {
  SUMMARY = "summary",
  INSIGHTS = "insights",
  RISKS = "risks",
  CONTRADICTIONS = "contradictions",
  NEXT_ACTIONS = "next_actions",
  EXECUTIVE_BRIEF = "executive_brief",
}

export interface WorkspaceSynthesis {
  synthesis_id: string;
  workspace_id: string;
  synthesis_type: SynthesisType;
  content: Record<string, unknown>;
  source_model?: string;
  generated_by?: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface GenerateSynthesisRequest {
  types?: SynthesisType[];
  model?: string;
  force_regenerate?: boolean;
}

export interface GenerateSynthesisResponse {
  workspace_id: string;
  results: WorkspaceSynthesis[];
}

export interface SynthesisContent {
  text?: string;
  summary?: string;
  insights?: string[];
  risks?: string[];
  contradictions?: Array<{
    hypothesis_id?: string;
    fact_index?: number;
    reason: string;
    severity: string;
  }>;
  next_actions?: Array<{
    action: string;
    reason: string;
    priority: string;
  }>;
  brief?: string;
}
