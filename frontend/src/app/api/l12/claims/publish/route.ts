/**
 * Layer 12: Collective Intelligence Exchange
 * API Route Handler - Publish Epistemic Artifact
 *
 * POST /api/l12/claims/publish
 */

import { NextRequest, NextResponse } from 'next/server';
import { createEpistemicArtifactPublisher } from '@/services/layer12/EpistemicArtifactPublisher';
import type { PublicationOptions } from '@/types/layer12/epistemic';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const { insightId, options }: { insightId: string; options: PublicationOptions } = body;

    // Validate input
    if (!insightId) {
      return NextResponse.json(
        { error: 'insightId is required' },
        { status: 400 }
      );
    }

    if (!options || !options.allowedUses || options.allowedUses.length === 0) {
      return NextResponse.json(
        { error: 'options.allowedUses is required and must not be empty' },
        { status: 400 }
      );
    }

    // TODO: Fetch insight from Layer 4
    // const insight = await insightService.getById(insightId);
    const insight = {
      insightId,
      type: 'best_practice',
      title: 'Sample Insight',
      summary: 'This is a sample insight for testing',
      description: 'Detailed description of the insight',
      confidence: 0.85,
      publishedAt: Date.now(),
      createdBy: 'system',
      domain: 'financial_planning',
      tags: ['planning', 'optimization']
    };

    // Get local node ID
    const localNodeId = process.env.TORQ_NODE_ID || 'node-local';

    // Create publisher service
    const publisher = createEpistemicArtifactPublisher(localNodeId);

    // Check if insight is federatable
    if (!publisher.isFederatable(insight)) {
      return NextResponse.json(
        {
          artifactId: null,
          status: 'rejected',
          errors: ['insight_not_federatable']
        },
        { status: 403 }
      );
    }

    // Publish artifact
    const result = await publisher.publishArtifact(insight, options);

    return NextResponse.json(result, {
      status: result.status === 'rejected' ? 422 : 200
    });

  } catch (error) {
    console.error('[L12 API] Error publishing claim:', error);
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
