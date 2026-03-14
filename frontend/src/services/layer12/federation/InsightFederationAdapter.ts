/**
 * Layer 12: Collective Intelligence Exchange
 * Phase 1B: Insight + Distributed Fabric Integration
 *
 * INSIGHT FEDERATION ADAPTER
 *
 * Transforms Layer 4 insights into Layer 12 federatable artifacts.
 * This is the bridge from local insight generation to network-wide claim exchange.
 */

import type { FederatedArtifactPayload, FederationEligibilityResult } from '../../types/layer12/federation';
import type { FederationConfig } from './FederationConfig';

/**
 * Layer 4 Insight record (placeholder - to be aligned with actual Layer 4 schema)
 */
export interface InsightRecord {
  insightId: string;
  claim: string;
  summary: string;
  domain: string;
  missionType: string;
  agentTopology: string;
  confidence: number;
  evidence: {
    sources: string[];
    sampleSize: number;
    methodology: string;
    stabilityScore?: number;
  };
  limitations: string[];
  sourceNode: string;
  sourceLayer: number;
  createdAt: number;
  classification?: 'public' | 'internal' | 'restricted';
  tags?: string[];
  isLocalOnly?: boolean;
  peerReviewed?: boolean;
  verified?: boolean;
}

/**
 * Draft artifact before redaction and metadata enrichment
 */
interface ArtifactDraft {
  artifactId: string;
  artifactType: 'observational' | 'pattern' | 'causal' | 'recommendation';
  claim: string;
  summary: string;
  context: Record<string, unknown>;
  evidence: {
    confidence: number;
    sources: string[];
    sampleSize: number;
    methodology: string;
    stabilityScore?: number;
  };
  limitations: string[];
  allowedUses: ('informational' | 'advisory' | 'simulation_tested' | 'allocative_eligible')[];
  provenance: {
    sourceNode: string;
    sourceLayer: number;
    timestamp: number;
    lineageId: string;
    verificationLevel?: 'none' | 'verified' | 'peer-reviewed';
  };
  redactedFields: string[];
}

/**
 * Insight Federation Adapter
 *
 * Transforms insights into federatable artifacts with eligibility checking,
 * redaction, and metadata enrichment.
 */
export class InsightFederationAdapter {
  private config: FederationConfig['eligibility'];

  constructor(config?: Partial<FederationConfig['eligibility']>) {
    // Default config will be provided by factory
    this.config = {
      minimumConfidence: 0.7,
      minimumProvenanceScore: 0.5,
      minimumSampleSize: 50,
      allowedDomains: [],
      restrictedDomains: [],
      requirePeerReview: true,
      requireVerification: false,
      maxArtifactAgeHours: 168,
      ...config
    };
  }

  /**
   * Main entry point: Transform insight into federatable artifact
   */
  async adaptInsightToArtifact(insight: InsightRecord): Promise<FederatedArtifactPayload | null> {
    // 1. Check eligibility
    const eligibility = await this.isFederationEligible(insight);
    if (!eligibility.eligible) {
      return null;
    }

    // 2. Determine artifact type
    const artifactType = this.determineArtifactType(insight);

    // 3. Create draft with full context
    const draft: ArtifactDraft = {
      artifactId: `artifact_${insight.insightId}`,
      artifactType,
      claim: insight.claim,
      summary: insight.summary,
      context: {
        domain: insight.domain,
        missionType: insight.missionType,
        agentTopology: insight.agentTopology,
        classification: insight.classification
      },
      evidence: {
        confidence: insight.confidence,
        sources: insight.evidence.sources,
        sampleSize: insight.evidence.sampleSize,
        methodology: insight.evidence.methodology,
        stabilityScore: insight.evidence.stabilityScore
      },
      limitations: insight.limitations,
      allowedUses: this.determineAllowedUses(insight, artifactType),
      provenance: {
        sourceNode: insight.sourceNode,
        sourceLayer: insight.sourceLayer,
        timestamp: insight.createdAt,
        lineageId: `lineage_${insight.insightId}`,
        verificationLevel: insight.verified ? 'verified' : (insight.peerReviewed ? 'peer-reviewed' : 'none')
      },
      redactedFields: eligibility.redactedFields || []
    };

    // 4. Apply redaction (in-place modification)
    this.redactForFederation(draft);

    // 5. Convert to federatable payload
    const payload: FederatedArtifactPayload = {
      artifactId: draft.artifactId,
      artifactType: draft.artifactType,
      title: draft.summary.substring(0, 200), // Use summary as title
      claimText: draft.claim,
      summary: draft.summary,
      confidence: draft.evidence.confidence,
      provenanceScore: this.computeProvenanceScore(insight),
      originLayer: draft.provenance.sourceLayer,
      originInsightId: insight.insightId,
      context: draft.context,
      limitations: draft.limitations,
      allowedUses: draft.allowedUses,
      tags: insight.tags,
      redactedFields: draft.redactedFields
    };

    return payload;
  }

  /**
   * Check if insight is eligible for federation
   */
  async isFederationEligible(insight: InsightRecord): Promise<FederationEligibilityResult> {
    const reasons: string[] = [];
    const redactedFields: string[] = [];

    // Check confidence threshold
    if (insight.confidence < this.config.minimumConfidence) {
      reasons.push(`confidence below threshold (${insight.confidence} < ${this.config.minimumConfidence})`);
    }

    // Check sample size
    if (insight.evidence.sampleSize < this.config.minimumSampleSize) {
      reasons.push(`sample size too small (${insight.evidence.sampleSize} < ${this.config.minimumSampleSize})`);
    }

    // Check peer review requirement
    if (this.config.requirePeerReview && !insight.peerReviewed) {
      reasons.push('not peer-reviewed');
    }

    // Check verification requirement
    if (this.config.requireVerification && !insight.verified) {
      reasons.push('not verified');
    }

    // Check classification restrictions
    if (insight.classification === 'restricted') {
      reasons.push('restricted classification');
      redactedFields.push('classification');
    }

    // Check domain restrictions
    if (this.config.restrictedDomains.includes(insight.domain)) {
      reasons.push(`restricted domain: ${insight.domain}`);
    }

    // Check local-only flag
    if (insight.isLocalOnly) {
      reasons.push('marked local-only');
    }

    // Check artifact age
    const ageHours = (Date.now() - insight.createdAt) / (1000 * 60 * 60);
    if (ageHours > this.config.maxArtifactAgeHours) {
      reasons.push(`artifact too old (${ageHours.toFixed(1)}h > ${this.config.maxArtifactAgeHours}h)`);
    }

    // Check allowed domains (if configured)
    if (this.config.allowedDomains.length > 0 && !this.config.allowedDomains.includes(insight.domain)) {
      reasons.push(`domain not in allowlist: ${insight.domain}`);
    }

    const eligible = reasons.length === 0;

    return {
      eligible,
      reasons,
      redactedFields
    };
  }

  /**
   * Determine artifact type from insight characteristics
   */
  private determineArtifactType(insight: InsightRecord): ArtifactDraft['artifactType'] {
    const hasCausalLanguage = /cause[s]?|result[s]?|lead[s]?|improve[s]?|worsen[s]?|affect[s]?/i.test(insight.claim);
    const hasRecommendation = /should|must|recommend|advise|use|avoid|adopt/i.test(insight.claim);
    const hasPattern = /pattern|correlation|tends to|when.*then/i.test(insight.claim);

    if (hasRecommendation) {
      return 'recommendation';
    } else if (hasCausalLanguage) {
      return 'causal';
    } else if (hasPattern) {
      return 'pattern';
    } else {
      return 'observational';
    }
  }

  /**
   * Determine allowed uses based on insight characteristics
   */
  private determineAllowedUses(
    insight: InsightRecord,
    artifactType: ArtifactDraft['artifactType']
  ): ArtifactDraft['allowedUses'] {
    const uses: ArtifactDraft['allowedUses'] = ['informational'];

    const highConfidence = insight.confidence >= 0.8;
    const largeSample = insight.evidence.sampleSize >= 1000;
    const verified = insight.verified || insight.peerReviewed;

    if (highConfidence && largeSample && verified) {
      uses.push('advisory');
    }

    if (highConfidence && verified && artifactType === 'recommendation') {
      uses.push('simulation_tested');
    }

    if (highConfidence && verified && largeSample && insight.evidence.stabilityScore && insight.evidence.stabilityScore >= 0.8) {
      uses.push('allocative_eligible');
    }

    return uses;
  }

  /**
   * Redact sensitive fields for federation
   */
  private redactForFederation(draft: ArtifactDraft): void {
    // Redact internal context
    if (draft.context.classification === 'internal') {
      delete draft.context.classification;
      if (!draft.redactedFields.includes('context.classification')) {
        draft.redactedFields.push('context.classification');
      }
    }

    // Redact local-only references
    const localKeys = Object.keys(draft.context).filter(k =>
      k.toLowerCase().includes('local') ||
      k.toLowerCase().includes('internal')
    );
    for (const key of localKeys) {
      delete draft.context[key];
      if (!draft.redactedFields.includes(`context.${key}`)) {
        draft.redactedFields.push(`context.${key}`);
      }
    }

    // Redact source-specific secrets if present
    if (draft.context.secrets) {
      delete draft.context.secrets;
      draft.redactedFields.push('context.secrets');
    }
  }

  /**
   * Compute provenance strength score (0-1)
   */
  private computeProvenanceScore(insight: InsightRecord): number {
    let score = 0.5; // Base score

    // Verification level
    if (insight.verified) {
      score += 0.3;
    } else if (insight.peerReviewed) {
      score += 0.2;
    }

    // Evidence quality
    if (insight.evidence.stabilityScore) {
      score += insight.evidence.stabilityScore * 0.1;
    }

    // Sample size (capped)
    const sampleBonus = Math.min(0.1, insight.evidence.sampleSize / 10000);
    score += sampleBonus;

    return Math.min(1, score);
  }

  /**
   * Build enriched metadata for federation
   */
  async buildArtifactMetadata(insight: InsightRecord): Promise<Record<string, unknown>> {
    return {
      sourceInsightId: insight.insightId,
      sourceNode: insight.sourceNode,
      sourceLayer: insight.sourceLayer,
      sourceClassification: insight.classification,
      adaptationCount: 0, // Will be incremented as claims move through nodes
      federatedAt: Date.now()
    };
  }
}

/**
 * Factory function
 */
export function createInsightFederationAdapter(
  config?: Partial<FederationConfig['eligibility']>
): InsightFederationAdapter {
  return new InsightFederationAdapter(config);
}
