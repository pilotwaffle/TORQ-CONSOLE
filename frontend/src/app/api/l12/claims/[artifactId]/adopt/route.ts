/**
 * Layer 12: Collective Intelligence Exchange
 * API Route Handler - Adopt Claim
 *
 * POST /api/l12/claims/[artifactId]/adopt
 */

import { NextRequest, NextResponse } from 'next/server';
import { createEpistemicAuditService } from '@/services/layer12';
import type { AllowedUse } from '@/types/layer12/epistemic';

export async function POST(
  request: NextRequest,
  { params }: { params: { artifactId: string } }
) {
  try {
    const { artifactId } = params;
    const body = await request.json();

    const {
      adoptionType,
      adaptations,
      nodeId
    }: {
      adoptionType: 'informational' | 'advisory' | 'simulation_tested' | 'allocative_eligible';
      adaptations?: string[];
      nodeId?: string;
    } = body;

    // Validate adoption type
    const validTypes: AllowedUse[] = ['informational', 'advisory', 'simulation_only', 'allocative_eligible'];
    const mappedType: AllowedUse = adoptionType === 'simulation_tested' ? 'simulation_only' : adoptionType;

    if (!validTypes.includes(mappedType)) {
      return NextResponse.json(
        { error: 'Invalid adoptionType', validTypes },
        { status: 400 }
      );
    }

    // Get local node ID
    const localNodeId = nodeId || process.env.TORQ_NODE_ID || 'node-local';

    // Create audit service
    const audit = createEpistemicAuditService();

    // Log adoption event
    await audit.logAdoption({
      artifactId,
      nodeId: localNodeId,
      adoptionType: mappedType,
      adaptations
    });

    // TODO: Store adoption in database
    // await adoptionService.recordAdoption(artifactId, localNodeId, adoptionType, adaptations);

    return NextResponse.json({
      artifactId,
      nodeId: localNodeId,
      adoptionType: mappedType,
      adoptedAt: Date.now(),
      status: 'adopted'
    });

  } catch (error) {
    console.error('[L12 API] Error adopting claim:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
