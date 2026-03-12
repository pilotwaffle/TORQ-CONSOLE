/**
 * Layer 12: Collective Intelligence Exchange
 * ContradictionAndPluralityManager Service
 *
 * Preserves disagreement instead of collapsing competing ideas.
 * Tracks when different nodes report conflicting patterns and maintains
 * plurality of interpretations.
 */

import { v4 as uuidv4 } from 'uuid';
import type {
  ContradictionRecord,
  ContradictionType,
  ResolutionType,
  EpistemicArtifact,
  PluralityView,
  CompetingClaim,
  ContradictionDetection,
  DetectedContradiction
} from '@/types/layer12/epistemic';

/**
 * Contradiction analysis result
 */
interface ContradictionAnalysis {
  hasContradiction: boolean;
  type?: ContradictionType;
  confidence: number;
  reasoning: string;
}

/**
 * Plurality preservation result
 */
interface PluralityPreservation {
  preserved: boolean;
  competingClaims: number;
  recommendedAction: 'preserve_plurality' | 'simulation_test' | 'governance_review';
}

/**
 * Service for managing contradictions and preserving plurality
 */
export class ContradictionAndPluralityManager {
  private contradictions: Map<string, ContradictionRecord> = new Map();
  private claimTopics: Map<string, Set<string>> = new Map(); // topic -> claim IDs

  constructor() {
    this.initializeIndexes();
  }

  /**
   * Register a contradiction between two claims
   */
  async registerContradiction(
    claimAId: string,
    claimBId: string,
    contradictionType: ContradictionType,
    detectedBy?: string
  ): Promise<ContradictionRecord> {
    const record: ContradictionRecord = {
      contradictionId: `contradiction_${uuidv4()}`,
      claimAId,
      claimBId,
      contradictionType,
      detectedAt: Date.now(),
      detectedBy: detectedBy || 'system',
      resolved: false
    };

    this.contradictions.set(record.contradictionId, record);

    // Index by topic
    const topicA = this.extractTopic(claimAId);
    const topicB = this.extractTopic(claimBId);

    if (topicA) {
      if (!this.claimTopics.has(topicA)) {
        this.claimTopics.set(topicA, new Set());
      }
      this.claimTopics.get(topicA)!.add(claimAId);
      this.claimTopics.get(topicA)!.add(claimBId);
    }

    await this.persistContradiction(record);

    return record;
  }

  /**
   * Detect contradictions automatically for a claim
   */
  async detectContradictions(
    claim: EpistemicArtifact,
    existingClaims: EpistemicArtifact[]
  ): Promise<ContradictionDetection> {
    const contradictions: DetectedContradiction[] = [];

    for (const existing of existingClaims) {
      // Skip self-comparison
      if (existing.artifactId === claim.artifactId) continue;

      // Analyze for contradiction
      const analysis = this.analyzeContradiction(claim, existing);

      if (analysis.hasContradiction && analysis.type) {
        contradictions.push({
          claimAId: claim.artifactId,
          claimBId: existing.artifactId,
          type: analysis.type,
          confidence: analysis.confidence
        });
      }
    }

    return {
      contradictions,
      pluralityPreserved: true // Always preserve plurality
    };
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
      .filter(r => !r.resolved)
      .sort((a, b) => b.detectedAt - a.detectedAt);
  }

  /**
   * Resolve a contradiction
   */
  async resolveContradiction(
    contradictionId: string,
    resolutionType: ResolutionType,
    resolutionNotes?: string
  ): Promise<void> {
    const record = this.contradictions.get(contradictionId);
    if (!record) {
      throw new Error(`Contradiction not found: ${contradictionId}`);
    }

    record.resolved = true;
    record.resolutionType = resolutionType;
    record.resolutionNotes = resolutionNotes;
    record.resolvedAt = Date.now();
    record.resolvedBy = 'system'; // TODO: Track actual resolver

    await this.persistContradiction(record);
  }

  /**
   * Get plurality view for a topic
   */
  async getPluralityView(topic: string): Promise<PluralityView> {
    const claimIds = this.claimTopics.get(topic);
    if (!claimIds || claimIds.size === 0) {
      return {
        topic,
        competingClaims: [],
        contradictionCount: 0,
        hasResolution: false,
        suggestedAction: 'preserve_plurality'
      };
    }

    // Build competing claims list
    // TODO: Fetch actual claim details from registry
    const competingClaims: CompetingClaim[] = [];
    let contradictionCount = 0;

    for (const claimId of claimIds) {
      // Check for contradictions
      const contradictions = await this.getContradictions(claimId);
      contradictionCount += contradictions.filter(c => !c.resolved).length;

      // competingClaims.push({
      //   claimId,
      //   claim: claim.summary,
      //   originNode: claim.originNode,
      //   confidence: claim.evidence.confidence,
      //   context: claim.context,
      //   supportingEvidence: claim.evidence.sampleSize || 0
      // });
    }

    // Determine suggested action
    let suggestedAction: PluralityView['suggestedAction'] = 'preserve_plurality';

    if (competingClaims.length < 2) {
      suggestedAction = 'preserve_plurality';
    } else if (contradictionCount > 0) {
      suggestedAction = 'simulation_test';
    } else if (competingClaims.length > 5) {
      suggestedAction = 'governance_review';
    }

    return {
      topic,
      competingClaims,
      contradictionCount,
      hasResolution: false,
      suggestedAction
    };
  }

  /**
   * Check if monoculture risk exists for a topic
   */
  async checkMonocultureRisk(
    topic: string,
    adoptionThreshold: number = 0.7
  ): Promise<{ hasMonocultureRisk: boolean; adoptionRate: number }> {
    const claimIds = this.claimTopics.get(topic);
    if (!claimIds || claimIds.size === 0) {
      return { hasMonocultureRisk: false, adoptionRate: 0 };
    }

    // TODO: Calculate actual adoption rates
    // For now, assume no monoculture if there are multiple claims
    const adoptionRate = claimIds.size > 1 ? 0.5 : 0.9;
    const hasMonocultureRisk = adoptionRate > adoptionThreshold && claimIds.size < 2;

    return { hasMonocultureRisk, adoptionRate };
  }

  /**
   * Get contradiction statistics
   */
  async getStatistics(): Promise<{
    totalContradictions: number;
    unresolvedContradictions: number;
    byType: Record<ContradictionType, number>;
    resolutionRate: number;
  }> {
    const byType: Record<ContradictionType, number> = {
      direct_contradiction: 0,
      context_conflict: 0,
      causal_disagreement: 0,
      recommendation_conflict: 0
    };

    let unresolved = 0;

    for (const record of this.contradictions.values()) {
      if (!record.resolved) {
        unresolved++;
      }
      byType[record.contradictionType]++;
    }

    const total = this.contradictions.size;
    const resolutionRate = total > 0 ? (total - unresolved) / total : 1;

    return {
      totalContradictions: total,
      unresolvedContradictions: unresolved,
      byType,
      resolutionRate
    };
  }

  /**
   * Analyze two claims for contradiction
   */
  private analyzeContradiction(
    claimA: EpistemicArtifact,
    claimB: EpistemicArtifact
  ): ContradictionAnalysis {
    // Check for direct contradiction (opposite claims)
    const directAnalysis = this.checkDirectContradiction(claimA, claimB);
    if (directAnalysis.hasContradiction) {
      return directAnalysis;
    }

    // Check for context conflict
    const contextAnalysis = this.checkContextConflict(claimA, claimB);
    if (contextAnalysis.hasContradiction) {
      return contextAnalysis;
    }

    // Check for causal disagreement
    const causalAnalysis = this.checkCausalDisagreement(claimA, claimB);
    if (causalAnalysis.hasContradiction) {
      return causalAnalysis;
    }

    // Check for recommendation conflict
    const recommendationAnalysis = this.checkRecommendationConflict(claimA, claimB);
    if (recommendationAnalysis.hasContradiction) {
      return recommendationAnalysis;
    }

    return {
      hasContradiction: false,
      confidence: 0,
      reasoning: 'no_contradiction_detected'
    };
  }

  /**
   * Check for direct contradiction (opposite claims)
   */
  private checkDirectContradiction(
    claimA: EpistemicArtifact,
    claimB: EpistemicArtifact
  ): ContradictionAnalysis {
    const claimAText = claimA.claim.toLowerCase();
    const claimBText = claimB.claim.toLowerCase();

    // Look for opposite sentiment patterns
    const positivePatterns = /\b(improves|enhances|increases|better|gains|optimizes)\b/i;
    const negativePatterns = /\b(degrades|reduces|decreases|worsens|losses|hinders)\b/i;

    const aIsPositive = positivePatterns.test(claimAText);
    const aIsNegative = negativePatterns.test(claimAText);
    const bIsPositive = positivePatterns.test(claimBText);
    const bIsNegative = negativePatterns.test(claimBText);

    // If one is positive and one is negative about the same thing
    if ((aIsPositive && bIsNegative) || (aIsNegative && bIsPositive)) {
      // Check if they're talking about the same subject
      const subjectA = this.extractSubject(claimA.claim);
      const subjectB = this.extractSubject(claimB.claim);

      if (subjectA === subjectB || this.similarSubjects(subjectA, subjectB)) {
        return {
          hasContradiction: true,
          type: 'direct_contradiction',
          confidence: Math.min(claimA.evidence.confidence, claimB.evidence.confidence),
          reasoning: `opposite_claims_about_same_subject: ${subjectA}`
        };
      }
    }

    return {
      hasContradiction: false,
      confidence: 0,
      reasoning: 'no_direct_contradiction'
    };
  }

  /**
   * Check for context conflict (same claim, different contexts)
   */
  private checkContextConflict(
    claimA: EpistemicArtifact,
    claimB: EpistemicArtifact
  ): ContradictionAnalysis {
    // Similar claims but different contexts
    const claimSimilarity = this.computeClaimSimilarity(claimA.claim, claimB.claim);

    if (claimSimilarity > 0.8) {
      // Check context differences
      const contextA = claimA.context;
      const contextB = claimB.context;

      if (contextA.domain && contextB.domain && contextA.domain !== contextB.domain) {
        return {
          hasContradiction: true,
          type: 'context_conflict',
          confidence: 0.7,
          reasoning: `similar_claim_different_domains: ${contextA.domain} vs ${contextB.domain}`
        };
      }

      if (contextA.regulatoryEnvironment && contextB.regulatoryEnvironment &&
          contextA.regulatoryEnvironment !== contextB.regulatoryEnvironment) {
        return {
          hasContradiction: true,
          type: 'context_conflict',
          confidence: 0.8,
          reasoning: `similar_claim_different_regulatory: ${contextA.regulatoryEnvironment} vs ${contextB.regulatoryEnvironment}`
        };
      }
    }

    return {
      hasContradiction: false,
      confidence: 0,
      reasoning: 'no_context_conflict'
    };
  }

  /**
   * Check for causal disagreement
   */
  private checkCausalDisagreement(
    claimA: EpistemicArtifact,
    claimB: EpistemicArtifact
  ): ContradictionAnalysis {
    // Check if both are causal claims with different conclusions
    if (claimA.artifactType === 'causal_claim' && claimB.artifactType === 'causal_claim') {
      const causeA = this.extractCause(claimA.claim);
      const causeB = this.extractCause(claimB.claim);
      const effectA = this.extractEffect(claimA.claim);
      const effectB = this.extractEffect(claimB.claim);

      // Same cause, different effects
      if (causeA === causeB && effectA !== effectB) {
        return {
          hasContradiction: true,
          type: 'causal_disagreement',
          confidence: 0.75,
          reasoning: `same_cause_different_effects: ${causeA} → ${effectA} vs ${effectB}`
        };
      }
    }

    return {
      hasContradiction: false,
      confidence: 0,
      reasoning: 'no_causal_disagreement'
    };
  }

  /**
   * Check for recommendation conflict
   */
  private checkRecommendationConflict(
    claimA: EpistemicArtifact,
    claimB: EpistemicArtifact
  ): ContradictionAnalysis {
    // Check if both are recommendations with opposite approaches
    if (claimA.artifactType === 'recommendation' && claimB.artifactType === 'recommendation') {
      const approachA = this.extractApproach(claimA.claim);
      const approachB = this.extractApproach(claimB.claim);

      // Check if approaches are opposites
      const opposites = [
        ['automate', 'manual'],
        ['centralize', 'decentralize'],
        ['optimize', 'simplify'],
        ['expand', 'reduce'],
        ['accelerate', 'delay']
      ];

      for (const [opposite1, opposite2] of opposites) {
        if ((approachA.includes(opposite1) && approachB.includes(opposite2)) ||
            (approachA.includes(opposite2) && approachB.includes(opposite1))) {
          return {
            hasContradiction: true,
            type: 'recommendation_conflict',
            confidence: 0.65,
            reasoning: `opposite_recommendations: ${opposite1} vs ${opposite2}`
          };
        }
      }
    }

    return {
      hasContradiction: false,
      confidence: 0,
      reasoning: 'no_recommendation_conflict'
    };
  }

  /**
   * Extract topic from claim ID or text
   */
  private extractTopic(claimId: string): string {
    // Extract topic from claim ID format
    const match = claimId.match(/artifact_(.+)/);
    if (match) {
      // Use first part before underscore as topic
      const parts = match[1].split('_');
      return parts[0];
    }
    return claimId.substring(0, 20);
  }

  /**
   * Extract subject from a claim
   */
  private extractSubject(claim: string): string {
    // Remove verbs and keep the core subject
    return claim
      .replace(/\b(improves|enhances|increases|degrades|reduces|decreases|worsens|optimizes|hinders)\b/gi, '')
      .replace(/\b(caused by|results in|leads to)\b/gi, '')
      .trim()
      .split(/\s+/)[0] || claim;
  }

  /**
   * Check if two subjects are similar
   */
  private similarSubjects(subjectA: string, subjectB: string): boolean {
    // Simple similarity check
    if (subjectA === subjectB) return true;
    if (subjectA.includes(subjectB) || subjectB.includes(subjectA)) return true;

    // Common synonyms
    const synonyms: Record<string, string[]> = {
      'performance': ['speed', 'efficiency', 'throughput'],
      'quality': ['accuracy', 'precision', 'correctness'],
      'cost': ['expense', 'spending', 'budget']
    };

    for (const [base, alternatives] of Object.entries(synonyms)) {
      if (alternatives.includes(subjectA) && alternatives.includes(subjectB)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Compute similarity between two claim texts
   */
  private computeClaimSimilarity(textA: string, textB: string): number {
    const wordsA = new Set(textA.toLowerCase().split(/\s+/));
    const wordsB = new Set(textB.toLowerCase().split(/\s+/));

    const intersection = new Set([...wordsA].filter(x => wordsB.has(x)));
    const union = new Set([...wordsA, ...wordsB]);

    return union.size > 0 ? intersection.size / union.size : 0;
  }

  /**
   * Extract cause from a causal claim
   */
  private extractCause(claim: string): string {
    const patterns = [
      /(\w+)\s+(caused|resulted in|led to)/i,
      /due to\s+(\w+)/i,
      /because of\s+(\w+)/i
    ];

    for (const pattern of patterns) {
      const match = claim.match(pattern);
      if (match) {
        return match[1];
      }
    }

    return '';
  }

  /**
   * Extract effect from a causal claim
   */
  private extractEffect(claim: string): string {
    const patterns = [
      /caused\s+(\w+)/i,
      /resulted in\s+(\w+)/i,
      /led to\s+(\w+)/i
    ];

    for (const pattern of patterns) {
      const match = claim.match(pattern);
      if (match) {
        return match[1];
      }
    }

    return '';
  }

  /**
   * Extract approach from a recommendation
   */
  private extractApproach(claim: string): string {
    // Remove common recommendation prefixes
    return claim
      .replace(/^(we recommend|suggest|should|consider|use)\s+/i, '')
      .trim()
      .split(/\s+/)[0] || claim;
  }

  /**
   * Initialize indexes
   */
  private initializeIndexes(): void {
    this.claimTopics = new Map();
  }

  /**
   * Persist contradiction to storage
   */
  private async persistContradiction(record: ContradictionRecord): Promise<void> {
    // TODO: Integrate with database layer
    console.log(`[L12] Persisting contradiction: ${record.contradictionId}`);
  }
}

/**
 * Export singleton instance factory
 */
export function createContradictionAndPluralityManager(): ContradictionAndPluralityManager {
  return new ContradictionAndPluralityManager();
}
