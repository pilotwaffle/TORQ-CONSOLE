/**
 * Layer 12: Collective Intelligence Exchange
 * API Route Handler - Get Artifact Audit Trail
 *
 * GET /api/l12/audit/artifact/[artifactId]
 */

import { NextRequest, NextResponse } from 'next/server';
import { createEpistemicAuditService } from '@/services/layer12';

export async function GET(
  request: NextRequest,
  { params }: { params: { artifactId: string } }
) {
  try {
    const { artifactId } = params;

    // Create audit service
    const audit = createEpistemicAuditService();

    // Get audit trail for artifact
    const trail = await audit.getArtifactAuditTrail(artifactId);

    // Verify completeness
    const completeness = await audit.verifyAuditCompleteness(artifactId);

    return NextResponse.json({
      artifactId,
      trail,
      completeness
    });

  } catch (error) {
    console.error('[L12 API] Error getting artifact audit trail:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
