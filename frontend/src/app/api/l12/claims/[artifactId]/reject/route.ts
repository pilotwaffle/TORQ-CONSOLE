/**
 * Layer 12: Collective Intelligence Exchange
 * API Route Handler - Reject Claim
 *
 * POST /api/l12/claims/[artifactId]/reject
 */

import { NextRequest, NextResponse } from 'next/server';
import { createEpistemicAuditService } from '@/services/layer12';

export async function POST(
  request: NextRequest,
  { params }: { params: { artifactId: string } }
) {
  try {
    const { artifactId } = params;
    const body = await request.json();

    const {
      reason,
      details,
      nodeId
    }: {
      reason: string;
      details?: string;
      nodeId?: string;
    } = body;

    // Validate input
    if (!reason) {
      return NextResponse.json(
        { error: 'reason is required' },
        { status: 400 }
      );
    }

    // Common rejection reasons
    const validReasons = [
      'low_confidence',
      'context_mismatch',
      'domain_mismatch',
      'policy_conflict',
      'has_contradictions',
      'insufficient_evidence',
      'stale_claim',
      'not_transferable'
    ];

    if (!validReasons.includes(reason)) {
      return NextResponse.json(
        { error: 'Invalid rejection reason', validReasons },
        { status: 400 }
      );
    }

    // Get local node ID
    const localNodeId = nodeId || process.env.TORQ_NODE_ID || 'node-local';

    // Create audit service
    const audit = createEpistemicAuditService();

    // Log rejection event
    await audit.logRejection({
      artifactId,
      nodeId: localNodeId,
      reason,
      details
    });

    // TODO: Store rejection in database
    // await rejectionService.recordRejection(artifactId, localNodeId, reason, details);

    return NextResponse.json({
      artifactId,
      nodeId: localNodeId,
      reason,
      rejectedAt: Date.now(),
      status: 'rejected'
    });

  } catch (error) {
    console.error('[L12 API] Error rejecting claim:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
