/**
 * Layer 12: Collective Intelligence Exchange
 * API Route Handler - Qualify Claim
 *
 * POST /api/l12/claims/qualify
 */

import { NextRequest, NextResponse } from 'next/server';
import { createLocalQualificationEngine } from '@/services/layer12/LocalQualificationEngine';
import { createFederatedClaimRegistry } from '@/services/layer12/FederatedClaimRegistry';
import type { LocalContext } from '@/types/layer12/epistemic';

export async function POST(
  request: NextRequest,
  { params }: { params: { artifactId: string } }
) {
  try {
    const { artifactId } = params;
    const body = await request.json();

    const { localContext }: { localContext: LocalContext } = body;

    // Validate input
    if (!localContext || !localContext.domain) {
      return NextResponse.json(
        { error: 'localContext.domain is required' },
        { status: 400 }
      );
    }

    // Fetch artifact from registry
    const registry = createFederatedClaimRegistry();
    const artifact = await registry.getClaim(artifactId);

    if (!artifact) {
      return NextResponse.json(
        { error: 'Artifact not found' },
        { status: 404 }
      );
    }

    // Create qualification engine
    const qualifier = createLocalQualificationEngine();

    // Qualify artifact
    const result = await qualifier.qualifyArtifact(
      {
        artifactId: artifact.artifactId,
        artifactType: artifact.artifactType,
        originNode: artifact.originNode,
        originLayer: artifact.originLayer,
        createdAt: artifact.createdAt,
        version: artifact.version,
        claim: artifact.claim,
        summary: artifact.summary,
        context: artifact.context,
        evidence: artifact.evidence,
        limitations: artifact.limitations,
        allowedUses: artifact.allowedUses,
        provenance: artifact.provenance,
        contradictions: undefined // Will be fetched separately if needed
      },
      localContext
    );

    return NextResponse.json({
      artifact: {
        artifactId: artifact.artifactId,
        claim: artifact.claim,
        summary: artifact.summary,
        originNode: artifact.originNode
      },
      qualifiedAt: Date.now(),
      ...result
    });

  } catch (error) {
    console.error('[L12 API] Error qualifying claim:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
