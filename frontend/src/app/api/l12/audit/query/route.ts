/**
 * Layer 12: Collective Intelligence Exchange
 * API Route Handler - Query Audit Log
 *
 * GET /api/l12/audit/query
 */

import { NextRequest, NextResponse } from 'next/server';
import { createEpistemicAuditService } from '@/services/layer12';
import type { AuditQuery } from '@/types/layer12/epistemic';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;

    // Build query from URL parameters
    const query: AuditQuery = {};

    if (searchParams.has('artifactId')) {
      query.artifactId = searchParams.get('artifactId')!;
    }

    if (searchParams.has('eventType')) {
      query.eventType = searchParams.get('eventType') as AuditQuery['eventType'];
    }

    if (searchParams.has('nodeId')) {
      query.nodeId = searchParams.get('nodeId')!;
    }

    if (searchParams.has('startDate')) {
      query.startDate = parseInt(searchParams.get('startDate')!);
    }

    if (searchParams.has('endDate')) {
      query.endDate = parseInt(searchParams.get('endDate')!);
    }

    // Create audit service
    const audit = createEpistemicAuditService();

    // Query audit log
    const events = await audit.queryAudit(query);

    return NextResponse.json({
      events,
      count: events.length,
      query
    });

  } catch (error) {
    console.error('[L12 API] Error querying audit log:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
