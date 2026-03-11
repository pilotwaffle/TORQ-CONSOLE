/**
 * API client for Reasoning Synthesis Engine
 */

import type {
  GenerateSynthesisRequest,
  GenerateSynthesisResponse,
  SynthesisType,
  WorkspaceSynthesis,
} from "./synthesisTypes";

const BASE = "/api/workspaces";

export async function generateSynthesis(
  workspaceId: string,
  options: GenerateSynthesisRequest = {}
): Promise<GenerateSynthesisResponse> {
  const response = await fetch(`${BASE}/${workspaceId}/syntheses/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      types: options.types || ["summary"],
      model: options.model,
      force_regenerate: options.force_regenerate ?? false,
    }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to generate synthesis: ${text}`);
  }
  return response.json() as Promise<GenerateSynthesisResponse>;
}

export async function listSyntheses(
  workspaceId: string
): Promise<WorkspaceSynthesis[]> {
  const response = await fetch(`${BASE}/${workspaceId}/syntheses`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to list syntheses: ${text}`);
  }
  return response.json() as Promise<WorkspaceSynthesis[]>;
}

export async function getLatestSynthesis(
  workspaceId: string,
  type: SynthesisType
): Promise<WorkspaceSynthesis> {
  const response = await fetch(`${BASE}/${workspaceId}/syntheses/latest?type=${type}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Synthesis not found");
    }
    const text = await response.text();
    throw new Error(`Failed to get latest synthesis: ${text}`);
  }
  return response.json() as Promise<WorkspaceSynthesis>;
}

export async function regenerateSynthesis(
  workspaceId: string,
  options: GenerateSynthesisRequest = {}
): Promise<GenerateSynthesisResponse> {
  const response = await fetch(`${BASE}/${workspaceId}/syntheses/regenerate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      types: options.types || ["summary"],
      model: options.model,
      force_regenerate: true,
    }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to regenerate synthesis: ${text}`);
  }
  return response.json() as Promise<GenerateSynthesisResponse>;
}
