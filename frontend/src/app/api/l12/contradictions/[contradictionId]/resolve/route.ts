/**
 * Layer 12: Collective Intelligence Exchange
 * API Route Handler - Resolve Contradiction
 *
 * POST /api/l12/contradictions/[contradictionId]/resolve
 */

import { NextRequest, NextResponse } from 'next/server';
import { createFederatedClaimRegistry } from '@/services/layer12/FederatedClaimRegistry';
import type { ResolutionType } from '@/types/layer12/epistemic';

export async function POST(
  request: NextRequest,
  { params }: { params: { contradictionId: string } }
) {
  try {
    const { contradictionId } = params;
    const body = await request.json();

    const {
      resolutionType,
      resolutionNotes
    }: {
      resolutionType: ResolutionType;
      resolutionNotes?: string;
    } = body;

    // Validate input
    const validTypes: ResolutionType[] = [
      'context_dependent',
      'simulation_resolved',
      'governance_resolved',
      'both_valid',
      'superseded'
    ];

    if (!resolutionType || !validTypes.includes(resolutionType)) {
      return NextResponse.json(
        { error: 'Invalid resolutionType', validTypes },
        { status: 400 }
      );
    }

    // Create registry service
    const registry = createFederatedClaimRegistry();

    // Resolve contradiction
    await registry.resolveContradiction(contradictionId, resolutionType, resolutionNotes);

    return NextResponse.json({
      contradictionId,
      resolutionType,
      resolvedAt: Date.now(),
      status: 'resolved'
    });

  } catch (error) {
    console.error('[L12 API] Error resolving contradiction:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
