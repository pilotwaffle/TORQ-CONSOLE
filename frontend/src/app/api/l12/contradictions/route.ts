/**
 * Layer 12: Collective Intelligence Exchange
 * API Route Handler - Register Contradiction
 *
 * POST /api/l12/contradictions
 */

import { NextRequest, NextResponse } from 'next/server';
import { createFederatedClaimRegistry } from '@/services/layer12/FederatedClaimRegistry';
import type { ContradictionType } from '@/types/layer12/epistemic';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const {
      claimAId,
      claimBId,
      contradictionType
    }: {
      claimAId: string;
      claimBId: string;
      contradictionType: ContradictionType;
    } = body;

    // Validate input
    if (!claimAId || !claimBId) {
      return NextResponse.json(
        { error: 'claimAId and claimBId are required' },
        { status: 400 }
      );
    }

    const validTypes: ContradictionType[] = [
      'direct_contradiction',
      'context_conflict',
      'causal_disagreement',
      'recommendation_conflict'
    ];

    if (!contradictionType || !validTypes.includes(contradictionType)) {
      return NextResponse.json(
        { error: 'Invalid contradictionType', validTypes },
        { status: 400 }
      );
    }

    // Create registry service
    const registry = createFederatedClaimRegistry();

    // Register contradiction
    const record = await registry.registerContradiction(
      claimAId,
      claimBId,
      contradictionType
    );

    return NextResponse.json({
      contradictionId: record.contradictionId,
      claimAId: record.claimAId,
      claimBId: record.claimBId,
      contradictionType: record.contradictionType,
      detectedAt: record.detectedAt,
      resolved: record.resolved,
      status: 'registered'
    });

  } catch (error) {
    console.error('[L12 API] Error registering contradiction:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
