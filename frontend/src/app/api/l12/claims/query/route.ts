/**
 * Layer 12: Collective Intelligence Exchange
 * API Route Handler - Query Claims
 *
 * GET /api/l12/claims/query
 */

import { NextRequest, NextResponse } from 'next/server';
import { createFederatedClaimRegistry } from '@/services/layer12/FederatedClaimRegistry';
import type { ClaimQuery } from '@/types/layer12/epistemic';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;

    // Build query from URL parameters
    const query: ClaimQuery = {};

    if (searchParams.has('artifactType')) {
      query.artifactType = searchParams.get('artifactType') as ClaimQuery['artifactType'];
    }

    if (searchParams.has('originNode')) {
      query.originNode = searchParams.get('originNode')!;
    }

    if (searchParams.has('domain')) {
      query.domain = searchParams.get('domain')!;
    }

    if (searchParams.has('missionType')) {
      query.missionType = searchParams.get('missionType')!;
    }

    if (searchParams.has('agentTopology')) {
      query.agentTopology = searchParams.get('agentTopology')!;
    }

    if (searchParams.has('minConfidence')) {
      query.minConfidence = parseFloat(searchParams.get('minConfidence')!);
    }

    if (searchParams.has('allowedUse')) {
      query.allowedUse = searchParams.get('allowedUse') as ClaimQuery['allowedUse'];
    }

    if (searchParams.has('limit')) {
      query.limit = parseInt(searchParams.get('limit')!, 10);
    }

    // Time range
    if (searchParams.has('startDate') && searchParams.has('endDate')) {
      query.timeRange = {
        start: parseInt(searchParams.get('startDate')!),
        end: parseInt(searchParams.get('endDate')!)
      };
    }

    // Create registry service
    const registry = createFederatedClaimRegistry();

    // Query claims
    const claims = await registry.queryClaims(query);

    // Get statistics
    const stats = await registry.getStatistics();

    return NextResponse.json({
      claims,
      total: claims.length,
      returned: claims.length,
      statistics: stats
    });

  } catch (error) {
    console.error('[L12 API] Error querying claims:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
