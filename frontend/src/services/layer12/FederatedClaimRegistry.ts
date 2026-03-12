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

/**
 * Service for managing federated epistemic claims
 */
export class FederatedClaimRegistry {
  private claims: Map<string, ClaimRecord> = new Map();
  private contradictions: Map<string, ContradictionRecord> = new Map();
  private contextIndex: Map<string, Set<string>> = new Map(); // domain -> claim IDs
  private originIndex: Map<string, Set<string>> = new Map(); // origin node -> claim IDs
  private typeIndex: Map<string, Set<string>> = new Map(); // artifact type -> claim IDs

  constructor() {
    // Initialize indexes
    this.initializeIndexes();
  }

  /**
   * Register a new claim in the registry
   */
  async registerClaim(artifact: EpistemicArtifact): Promise<ClaimRecord> {
    const record: ClaimRecord = {
      artifactId: artifact.artifactId,
      artifactType: artifact.artifactType,
      originNode: artifact.originNode,
      originLayer: artifact.originLayer,
      createdAt: artifact.createdAt,
      version: artifact.version,
      claim: artifact.claim,
      summary: artifact.summary,
      context: artifact.context,
      evidence: artifact.evidence,
      limitations: artifact.limitations,
      allowedUses: artifact.allowedUses,
      provenance: artifact.provenance,
      receivedAt: Date.now(),
      indexedAt: Date.now()
    };

    // Store claim
    this.claims.set(artifact.artifactId, record);

    // Update indexes
    this.updateIndexes(record);

    // Persist to database
    await this.persistClaim(record);

    return record;
  }

  /**
   * Query claims with context filters
   */
  async queryClaims(query: ClaimQuery): Promise<ClaimRecord[]> {
    let results = Array.from(this.claims.values());

    // Filter by artifact type
    if (query.artifactType) {
      results = results.filter(r => r.artifactType === query.artifactType);
    }

    // Filter by origin node
    if (query.originNode) {
      results = results.filter(r => r.originNode === query.originNode);
    }

    // Filter by domain
    if (query.domain) {
      results = results.filter(r => r.context.domain === query.domain);
    }

    // Filter by mission type
    if (query.missionType) {
      results = results.filter(r => r.context.missionType === query.missionType);
    }

    // Filter by agent topology
    if (query.agentTopology) {
      results = results.filter(r => r.context.agentTopology === query.agentTopology);
    }

    // Filter by minimum confidence
    if (query.minConfidence !== undefined) {
      results = results.filter(r => r.evidence.confidence >= query.minConfidence);
    }

    // Filter by allowed use
    if (query.allowedUse) {
      results = results.filter(r => r.allowedUses.includes(query.allowedUse));
    }

    // Filter by time range
    if (query.timeRange) {
      results = results.filter(r =>
        r.createdAt >= query.timeRange!.start &&
        r.createdAt <= query.timeRange!.end
      );
    }

    // Apply limit
    if (query.limit && results.length > query.limit) {
      results = results.slice(0, query.limit);
    }

    return results;
  }

  /**
   * Retrieve specific claim by ID
   */
  async getClaim(claimId: string): Promise<ClaimRecord | null> {
    return this.claims.get(claimId) || null;
  }

  /**
   * Find claims by relevance to local context
   */
  async findRelevantClaims(localContext: LocalContext): Promise<ClaimRecord[]> {
    const relevantClaims: Array<{ claim: ClaimRecord; score: number }> = [];

    for (const claim of this.claims.values()) {
      const score = this.computeRelevanceScore(claim, localContext);
      if (score > 0.3) { // Minimum relevance threshold
        relevantClaims.push({ claim, score });
      }
    }

    // Sort by relevance score descending
    relevantClaims.sort((a, b) => b.score - a.score);

    return relevantClaims.map(r => r.claim);
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

    this.contradictions.set(record.contradictionId, record);

    // Update claim records with contradiction references
    const claimA = this.claims.get(claimAId);
    const claimB = this.claims.get(claimBId);

    if (claimA && !claimA.limitations) {
      claimA.limitations = [];
    }
    if (claimB && !claimB.limitations) {
      claimB.limitations = [];
    }

    if (claimA) {
      claimA.limitations?.push(`contradicted_by_${claimBId}`);
    }
    if (claimB) {
      claimB.limitations?.push(`contradicted_by_${claimAId}`);
    }

    await this.persistContradiction(record);

    return record;
  }

  /**
   * Get contradictions for a specific claim
   */
  async getContradictions(claimId: string): Promise<ContradictionRecord[]> {
    const contradictions: ContradictionRecord[] = [];

    for (const record of this.contradictions.values()) {
      if (record.claimAId === claimId || record.claimBId === claimId) {
        contradictions.push(record);
      }
    }

    return contradictions;
  }

  /**
   * Get all unresolved contradictions
   */
  async getUnresolvedContradictions(): Promise<ContradictionRecord[]> {
    return Array.from(this.contradictions.values())
      .filter(r => !r.resolved);
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
    byType: Record<string, number>;
    byOrigin: Record<string, number>;
    byDomain: Record<string, number>;
    contradictionCount: number;
    unresolvedContradictionCount: number;
  }> {
    const byType: Record<string, number> = {};
    const byOrigin: Record<string, number> = {};
    const byDomain: Record<string, number> = {};

    for (const claim of this.claims.values()) {
      // Count by type
      byType[claim.artifactType] = (byType[claim.artifactType] || 0) + 1;

      // Count by origin
      byOrigin[claim.originNode] = (byOrigin[claim.originNode] || 0) + 1;

      // Count by domain
      if (claim.context.domain) {
        byDomain[claim.context.domain] = (byDomain[claim.context.domain] || 0) + 1;
      }
    }

    return {
      totalClaims: this.claims.size,
      byType,
      byOrigin,
      byDomain,
      contradictionCount: this.contradictions.size,
      unresolvedContradictionCount: Array.from(this.contradictions.values())
        .filter(r => !r.resolved).length
    };
  }

  /**
   * Initialize indexes
   */
  private initializeIndexes(): void {
    this.contextIndex = new Map();
    this.originIndex = new Map();
    this.typeIndex = new Map();
  }

  /**
   * Update indexes for a new claim
   */
  private updateIndexes(record: ClaimRecord): void {
    // Domain index
    if (record.context.domain) {
      if (!this.contextIndex.has(record.context.domain)) {
        this.contextIndex.set(record.context.domain, new Set());
      }
      this.contextIndex.get(record.context.domain)!.add(record.artifactId);
    }

    // Origin node index
    if (!this.originIndex.has(record.originNode)) {
      this.originIndex.set(record.originNode, new Set());
    }
    this.originIndex.get(record.originNode)!.add(record.artifactId);

    // Artifact type index
    if (!this.typeIndex.has(record.artifactType)) {
      this.typeIndex.set(record.artifactType, new Set());
    }
    this.typeIndex.get(record.artifactType)!.add(record.artifactId);
  }

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

  /**
   * Persist claim to database
   */
  private async persistClaim(record: ClaimRecord): Promise<void> {
    // TODO: Integrate with database layer
    console.log(`[L12] Persisting claim: ${record.artifactId}`);
  }

  /**
   * Persist contradiction to database
   */
  private async persistContradiction(record: ContradictionRecord): Promise<void> {
    // TODO: Integrate with database layer
    console.log(`[L12] Persisting contradiction: ${record.contradictionId}`);
  }
}

/**
 * Export singleton instance factory
 */
export function createFederatedClaimRegistry(): FederatedClaimRegistry {
  return new FederatedClaimRegistry();
}
