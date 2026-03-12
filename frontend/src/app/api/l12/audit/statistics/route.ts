/**
 * Layer 12: Collective Intelligence Exchange
 * API Route Handler - Get Adoption Statistics
 *
 * GET /api/l12/audit/statistics
 */

import { NextRequest, NextResponse } from 'next/server';
import { createEpistemicAuditService } from '@/services/layer12';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;

    const nodeId = searchParams.get('nodeId') || process.env.TORQ_NODE_ID || 'node-local';
    const startDate = searchParams.has('startDate') ? parseInt(searchParams.get('startDate')!) : undefined;
    const endDate = searchParams.has('endDate') ? parseInt(searchParams.get('endDate')!) : undefined;

    // Create audit service
    const audit = createEpistemicAuditService();

    // Get adoption statistics
    const stats = await audit.getAdoptionStats(nodeId, startDate, endDate);

    // Also get node statistics
    const nodeStats = await audit.getNodeStatistics(nodeId);

    return NextResponse.json({
      nodeId,
      timeRange: { startDate, endDate },
      adoption: stats,
      node: nodeStats
    });

  } catch (error) {
    console.error('[L12 API] Error getting statistics:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
