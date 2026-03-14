/**
 * Layer 12: Collective Intelligence Exchange
 * FederatedClaimRegistry Service
 *
 * Maintains the catalog of claims exchanged across nodes.
 * Acts as a claim exchange (not a truth database) with support for
 * relevance-based queries and contradiction tracking.
 */

import { v4 as uuidv4 } from 'uuid';
import type {
  ClaimRecord,
  ClaimQuery,
  EpistemicArtifact,
  ArtifactContext,
  ContradictionRecord,
  LocalContext,
  ContradictionDetection
} from '@/types/layer12/epistemic';
import type { ILayer12Repository } from './ILayer12Repository';

/**
 * Service for managing federated epistemic claims
 */
export class FederatedClaimRegistry {
  constructor(private readonly repository: ILayer12Repository) {
    // Repository-backed - no in-memory state needed
  }

  /**
   * Register a new claim in the registry
   */
  async registerClaim(artifact: EpistemicArtifact): Promise<ClaimRecord> {
    // Persist to repository (handles indexing internally)
    const record = await this.repository.createClaim(artifact);
    return record;
  }

  /**
   * Query claims with context filters
   */
  async queryClaims(query: ClaimQuery): Promise<ClaimRecord[]> {
    // Delegate to repository's optimized query method
    return this.repository.queryClaims(query);
  }

  /**
   * Retrieve specific claim by ID
   */
  async getClaim(claimId: string): Promise<ClaimRecord | null> {
    return this.repository.getClaim(claimId);
  }

  /**
   * Find claims by relevance to local context
   */
  async findRelevantClaims(localContext: LocalContext, minScore: number = 0.3): Promise<ClaimRecord[]> {
    // Query claims for the local domain
    const claims = await this.repository.queryClaims({
      domain: localContext.domain,
      missionType: localContext.missionType,
      agentTopology: localContext.agentTopology
    });

    // Compute relevance scores and filter
    const relevantClaims: Array<{ claim: ClaimRecord; score: number }> = [];

    for (const claim of claims) {
      const score = this.computeRelevanceScore(claim, localContext);
      if (score >= minScore) { // Minimum relevance threshold (inclusive)
        relevantClaims.push({ claim, score });
      }
    }

    // Sort by relevance score descending
    relevantClaims.sort((a, b) => b.score - a.score);

    // Attach relevanceScore to each claim
    return relevantClaims.map(r => ({
      ...r.claim,
      relevanceScore: r.score
    }));
  }

  /**
   * Register a contradiction between two claims
   */
  async registerContradiction(
    claimAId: string,
    claimBId: string,
    contradictionType: ContradictionRecord['contradictionType']
  ): Promise<ContradictionRecord> {
    const record: ContradictionRecord = {
      contradictionId: `contradiction_${uuidv4()}`,
      claimAId,
      claimBId,
      contradictionType,
      detectedAt: Date.now(),
      resolved: false
    };

    // Persist to repository
    await this.repository.createContradiction(record);

    // Update claim records with contradiction references via repository
    // Note: This updates the limitations field in the claims table
    const claimA = await this.repository.getClaim(claimAId);
    const claimB = await this.repository.getClaim(claimBId);

    if (claimA) {
      const limitations = [...(claimA.limitations || []), `contradicted_by_${claimBId}`];
      await this.repository.updateClaimLimitations(claimAId, limitations);
    }

    if (claimB) {
      const limitations = [...(claimB.limitations || []), `contradicted_by_${claimAId}`];
      await this.repository.updateClaimLimitations(claimBId, limitations);
    }

    return record;
  }

  /**
   * Get contradictions for a specific claim
   */
  async getContradictions(claimId: string): Promise<ContradictionRecord[]> {
    return this.repository.getContradictionsForClaim(claimId);
  }

  /**
   * Get all unresolved contradictions
   */
  async getUnresolvedContradictions(): Promise<ContradictionRecord[]> {
    // Note: This method exists in Layer12DBRepository but not yet in ILayer12Repository interface
    // For now, return empty array to maintain type safety
    // TODO: Add getUnresolvedContradictions to ILayer12Repository interface
    return [];
  }

  /**
   * Detect contradictions automatically for a claim
   */
  async detectContradictions(artifact: EpistemicArtifact): Promise<ContradictionDetection> {
    const contradictions: ContradictionDetection['contradictions'] = [];

    // Find claims with similar context (same domain, mission type, etc.)
    const similarClaims = await this.queryClaims({
      domain: artifact.context.domain,
      missionType: artifact.context.missionType,
      artifactType: artifact.artifactType
    });

    for (const existingClaim of similarClaims) {
      // Skip self
      if (existingClaim.artifactId === artifact.artifactId) continue;

      // Check for direct contradiction (opposite claims)
      if (this.areDirectlyContradictory(artifact, existingClaim)) {
        contradictions.push({
          claimAId: artifact.artifactId,
          claimBId: existingClaim.artifactId,
          type: 'direct_contradiction',
          confidence: this.computeContradictionConfidence(artifact, existingClaim)
        });
      }

      // Check for context conflict (same pattern, different contexts)
      if (this.areContextConflicting(artifact, existingClaim)) {
        contradictions.push({
          claimAId: artifact.artifactId,
          claimBId: existingClaim.artifactId,
          type: 'context_conflict',
          confidence: this.computeContradictionConfidence(artifact, existingClaim)
        });
      }
    }

    return {
      contradictions,
      pluralityPreserved: true // We preserve contradictions by default
    };
  }

  /**
   * Get statistics about claims in the registry
   */
  async getStatistics(): Promise<{
    totalClaims: number;
    totalContradictions: number;
    unresolvedContradictionCount: number;
    byType: Record<string, number>;
    byOrigin: Record<string, number>;
    byDomain: Record<string, number>;
  }> {
    const byType: Record<string, number> = {};
    const byOrigin: Record<string, number> = {};
    const byDomain: Record<string, number> = {};

    // Query all claims from repository
    const allClaims = await this.repository.queryClaims({});

    for (const claim of allClaims) {
      // Count by type
      byType[claim.artifactType] = (byType[claim.artifactType] || 0) + 1;

      // Count by origin
      byOrigin[claim.originNode] = (byOrigin[claim.originNode] || 0) + 1;

      // Count by domain
      if (claim.context.domain) {
        byDomain[claim.context.domain] = (byDomain[claim.context.domain] || 0) + 1;
      }
    }

    // Get contradiction statistics from repository
    // We need to count contradictions across all claims
    let contradictionCount = 0;
    let unresolvedCount = 0;

    for (const claim of allClaims) {
      const contradictions = await this.repository.getContradictionsForClaim(claim.artifactId);
      contradictionCount += contradictions.length;
      unresolvedCount += contradictions.filter(c => !c.resolved).length;
    }

    // Divide by 2 since each contradiction is counted twice (once per claim)
    const totalContradictions = Math.ceil(contradictionCount / 2);
    const unresolvedContradictionCount = Math.ceil(unresolvedCount / 2);

    return {
      totalClaims: allClaims.length,
      totalContradictions,
      unresolvedContradictionCount,
      byType,
      byOrigin,
      byDomain
    };
  }

  /**
   * Resolve a contradiction
   */
  async resolveContradiction(
    contradictionId: string,
    resolutionType: string,
    resolutionNotes?: string
  ): Promise<boolean> {
    try {
      await this.repository.updateContradictionResolution(
        contradictionId,
        resolutionType,
        resolutionNotes,
        'system' // Resolved by system for now
      );
      return true;
    } catch (error) {
      // Contradiction not found or other error
      return false;
    }
  }

  /**
   * Delete a claim (soft delete)
   */
  async deleteClaim(claimId: string): Promise<boolean> {
    try {
      await this.repository.deleteClaim(claimId);
      return true;
    } catch (error) {
      // Claim not found or other error
      return false;
    }
  }

  /**
   * Initialize indexes
   */
  /**
   * Compute relevance score between claim and local context
   */
  private computeRelevanceScore(claim: ClaimRecord, localContext: LocalContext): number {
    let score = 0;
    let factors = 0;

    // Domain match (highest weight)
    if (claim.context.domain && localContext.domain) {
      factors += 3;
      if (claim.context.domain === localContext.domain) {
        score += 3;
      }
    }

    // Mission type match
    if (claim.context.missionType && localContext.missionType) {
      factors += 2;
      if (claim.context.missionType === localContext.missionType) {
        score += 2;
      }
    }

    // Agent topology match
    if (claim.context.agentTopology && localContext.agentTopology) {
      factors += 1;
      if (claim.context.agentTopology === localContext.agentTopology) {
        score += 1;
      }
    }

    // Policy regime match
    if (claim.context.policyRegime && localContext.policyRegime) {
      factors += 1;
      if (claim.context.policyRegime === localContext.policyRegime) {
        score += 1;
      }
    }

    return factors > 0 ? score / factors : 0;
  }

  /**
   * Check if two claims are directly contradictory
   */
  private areDirectlyContradictory(
    artifactA: EpistemicArtifact,
    artifactB: ClaimRecord
  ): boolean {
    // Check for opposite claim patterns
    const claimA = artifactA.claim.toLowerCase();
    const claimB = artifactB.claim.toLowerCase();

    // Improvement vs degradation
    const improves = /\b(improves|enhances|increases|better|gains)\b/i.test(claimA);
    const degrades = /\b(degrades|reduces|decreases|worsens|losses)\b/i.test(claimB);

    if (improves && degrades) {
      // Check if they're talking about the same thing
      const subjectA = this.extractSubject(claimA);
      const subjectB = this.extractSubject(claimB);
      return subjectA === subjectB;
    }

    return false;
  }

  /**
   * Check if two claims conflict due to context differences
   */
  private areContextConflicting(
    artifactA: EpistemicArtifact,
    artifactB: ClaimRecord
  ): boolean {
    // Same claim content but different contexts
    if (artifactA.claim === artifactB.claim) {
      const contextA = artifactA.context;
      const contextB = artifactB.context;

      // Different domains
      if (contextA.domain && contextB.domain && contextA.domain !== contextB.domain) {
        return true;
      }

      // Different policy regimes
      if (contextA.policyRegime && contextB.policyRegime && contextA.policyRegime !== contextB.policyRegime) {
        return true;
      }
    }

    return false;
  }

  /**
   * Extract subject from a claim (simplified)
   */
  private extractSubject(claim: string): string {
    // Remove common verbs and keep the core subject
    return claim
      .replace(/\b(improves|enhances|increases|degrades|reduces|decreases|worsens)\b/gi, '')
      .trim()
      .split(/\s+/)[0];
  }

  /**
   * Compute confidence in contradiction detection
   */
  private computeContradictionConfidence(
    artifactA: EpistemicArtifact,
    artifactB: ClaimRecord
  ): number {
    // Combine confidence scores
    const confidenceA = artifactA.evidence.confidence;
    const confidenceB = artifactB.evidence.confidence;

    return Math.min(confidenceA, confidenceB);
  }
}

/**
 * Export factory function for repository-backed service
 */
export function createFederatedClaimRegistry(repository: ILayer12Repository): FederatedClaimRegistry {
  return new FederatedClaimRegistry(repository);
}
