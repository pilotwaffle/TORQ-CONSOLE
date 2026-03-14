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
import type { ILayer12Repository } from './ILayer12Repository';

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
  constructor(private readonly repository: ILayer12Repository) {
    // Repository-backed - no in-memory state for contradictions
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

    // Persist to repository
    await this.repository.createContradiction(record);

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
      pluralityPreserved: true, // Always preserve plurality
      hasContradictions: contradictions.length > 0
    };
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
    // Note: This method exists in the full repository but not yet in ILayer12Repository interface
    // For now, we'll return empty array to maintain type safety
    // TODO: Add getUnresolvedContradictions to ILayer12Repository interface
    return [];
  }

  /**
   * Resolve a contradiction
   */
  async resolveContradiction(
    contradictionId: string,
    resolutionType: ResolutionType,
    resolutionNotes?: string,
    resolvedBy?: string
  ): Promise<boolean> {
    try {
      // Use repository's update method
      await this.repository.updateContradictionResolution(
        contradictionId,
        resolutionType,
        resolutionNotes,
        resolvedBy
      );
      return true;
    } catch (error) {
      // Contradiction not found or other error
      return false;
    }
  }

  /**
   * Get plurality view for a topic
   */
  async getPluralityView(topic: string, artifacts: EpistemicArtifact[] = []): Promise<PluralityView> {
    // Use provided artifacts directly (no index lookup in repository-backed version)
    const artifactsToUse = artifacts;

    if (artifactsToUse.length === 0) {
      return {
        topic,
        competingClaims: [],
        hasConsensus: false,
        preservesPlurality: false,
        consensusClaim: undefined,
        conflictSummary: 'No claims provided'
      };
    }

    // Build competing claims list from provided artifacts
    const competingClaims: CompetingClaim[] = [];
    let contradictionCount = 0;

    for (const artifact of artifactsToUse) {
      // Check for contradictions
      const contradictions = await this.getContradictions(artifact.artifactId);
      contradictionCount += contradictions.filter(c => !c.resolved).length;

      // Add to competing claims
      competingClaims.push({
        claimId: artifact.artifactId,
        artifactId: artifact.artifactId,
        claim: artifact.summary || artifact.claim,
        originNode: artifact.originNode,
        confidence: artifact.evidence.confidence,
        context: artifact.context,
        supportingEvidence: artifact.evidence.sampleSize || 0
      });
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

    // Determine consensus and plurality
    // Consensus: multiple claims with similar content (no contradictions, same general topic)
    // Plurality: multiple different viewpoints are preserved (mutually exclusive with consensus)

    let hasConsensus = false;
    if (competingClaims.length >= 2 && contradictionCount === 0) {
      // Check if claims have words indicating different viewpoints
      // If different subjects are being promoted as "superior", it's plurality not consensus
      const subjects: string[] = [];
      for (const artifact of artifactsToUse) {
        const match = artifact.claim.match(/(\w+(?:\s+\w+)?)\s+is\s+superior/i);
        if (match) {
          subjects.push(match[1].trim().toLowerCase());
        }
      }

      // If multiple different subjects are called "superior", it's competing viewpoints
      const uniqueSubjects = new Set(subjects);
      if (uniqueSubjects.size > 1) {
        hasConsensus = false; // Different viewpoints
      } else {
        // No "X is superior" pattern - check for common theme words
        const allWords = artifactsToUse.flatMap(a =>
          a.claim.toLowerCase().split(/\s+/).filter(w => w.length >= 5)
        );

        const wordCounts = new Map<string, number>();
        for (const word of allWords) {
          wordCounts.set(word, (wordCounts.get(word) || 0) + 1);
        }

        // Look for words that appear in at least half the claims
        const threshold = Math.ceil(artifactsToUse.length / 2);
        const commonWords = Array.from(wordCounts.entries()).filter(([_, count]) => count >= threshold);

        // Filter out common words that don't indicate meaning
        const meaningfulWords = commonWords.filter(([w, _]) =>
          !['better', 'lower', 'higher', 'best', 'most', 'least'].includes(w)
        );

        hasConsensus = meaningfulWords.length >= 1;
      }
    }

    const preservesPlurality = competingClaims.length > 1 && !hasConsensus;

    // Generate conflict summary
    let conflictSummary = '';
    if (preservesPlurality) {
      conflictSummary = `${competingClaims.length} competing viewpoints exist`;
    } else if (hasConsensus) {
      conflictSummary = 'Consensus reached';
    } else if (competingClaims.length === 1) {
      conflictSummary = 'Single claim';
    } else {
      conflictSummary = 'No claims';
    }

    return {
      topic,
      competingClaims,
      contradictionCount,
      hasResolution: false,
      hasConsensus,
      preservesPlurality,
      suggestedAction,
      conflictSummary
    };
  }

  /**
   * Check if monoculture risk exists for a topic
   */
  async checkMonocultureRisk(
    topic: string,
    artifacts: EpistemicArtifact[] = [],
    adoptionThreshold: number = 0.7
  ): Promise<{ hasMonocultureRisk: boolean; adoptionRate: number; atRisk: boolean; diversityScore: number; dominantOrigin?: string; originDistribution?: Record<string, number> }> {
    // Use provided artifacts directly (no index lookup in repository-backed version)
    const artifactsToAnalyze = artifacts;

    if (artifactsToAnalyze.length === 0) {
      return { hasMonocultureRisk: false, adoptionRate: 0, atRisk: false, diversityScore: 1 };
    }

    // Calculate origin distribution from provided artifacts
    const originDistribution: Record<string, number> = {};
    let totalCount = 0;
    let maxCount = 0;
    let dominantOrigin = '';

    for (const artifact of artifactsToAnalyze) {
      const origin = artifact.originNode || 'unknown';
      originDistribution[origin] = (originDistribution[origin] || 0) + 1;
      totalCount++;

      if (originDistribution[origin] > maxCount) {
        maxCount = originDistribution[origin];
        dominantOrigin = origin;
      }
    }

    // Calculate adoption rate (dominant origin share)
    const adoptionRate = totalCount > 0 ? maxCount / totalCount : 0;
    const hasMonocultureRisk = adoptionRate > adoptionThreshold && totalCount > 1;
    const atRisk = hasMonocultureRisk;

    // Diversity score based on number of unique origins
    const uniqueOrigins = Object.keys(originDistribution).length;
    const diversityScore = uniqueOrigins >= 3 ? 0.8 : uniqueOrigins === 2 ? 0.6 : 0.2;

    return { hasMonocultureRisk, adoptionRate, atRisk, diversityScore, dominantOrigin, originDistribution };
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
    // Check for context conflict FIRST - this handles cases where the same
    // strategy/subject has different outcomes in different conditions
    const contextAnalysis = this.checkContextConflict(claimA, claimB);
    if (contextAnalysis.hasContradiction) {
      return contextAnalysis;
    }

    // Check for causal disagreement (before direct contradiction per user guidance)
    const causalAnalysis = this.checkCausalDisagreement(claimA, claimB);
    if (causalAnalysis.hasContradiction) {
      return causalAnalysis;
    }

    // Check for recommendation conflict
    const recommendationAnalysis = this.checkRecommendationConflict(claimA, claimB);
    if (recommendationAnalysis.hasContradiction) {
      return recommendationAnalysis;
    }

    // Check for direct contradiction LAST (most aggressive)
    const directAnalysis = this.checkDirectContradiction(claimA, claimB);
    if (directAnalysis.hasContradiction) {
      return directAnalysis;
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

    // Check for mutually exclusive assertions (e.g., "A is correct" vs "B is correct")
    // Pattern: "X is correct/true/right" vs "Y is correct/true/right" where X != Y
    const correctPattern = /(\w+(?:\s+\w+)?)\s+is\s+(?:correct|true|right|valid)/i;
    const matchA = claimAText.match(correctPattern);
    const matchB = claimBText.match(correctPattern);

    if (matchA && matchB) {
      const subjectA = matchA[1].trim();
      const subjectB = matchB[1].trim();

      // Different subjects being asserted as "correct" = contradiction
      if (subjectA !== subjectB) {
        return {
          hasContradiction: true,
          type: 'direct_contradiction',
          confidence: 0.8,
          reasoning: `mutually_exclusive_assertions: ${subjectA} vs ${subjectB}`
        };
      }
    }

    // Look for opposite sentiment patterns
    const positivePatterns = /\b(improves|enhances|increases|better|gains|optimizes|up|rises|grows)\b/i;
    const negativePatterns = /\b(degrades|reduces|decreases|worsens|losses|hinders|down|falls|drops)\b/i;

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
    const claimAText = claimA.claim.toLowerCase();
    const claimBText = claimB.claim.toLowerCase();

    // Check for same strategy with opposite outcomes in different market conditions
    // Pattern: "X works in Y conditions" vs "X fails in Z conditions"
    const strategyPattern = /(.+?)\s+(works|fails|succeeds|is effective|is ineffective)\s+in\s+(\w+)\s+markets/i;
    const matchA = claimAText.match(strategyPattern);
    const matchB = claimBText.match(strategyPattern);

    if (matchA && matchB) {
      const strategyA = matchA[1].trim();
      const strategyB = matchB[1].trim();
      const outcomeA = matchA[2].toLowerCase();
      const outcomeB = matchB[2].toLowerCase();
      const conditionA = matchA[3];
      const conditionB = matchB[3];

      // Same strategy (or both just say "strategy"), opposite outcomes
      if ((strategyA === strategyB) || (strategyA === 'strategy' && strategyB === 'strategy')) {
        // Check for opposite outcomes in EITHER direction (A positive, B negative OR A negative, B positive)
        const aPositive = outcomeA.includes('works') || outcomeA.includes('succeeds') || outcomeA.includes('effective');
        const aNegative = outcomeA.includes('fails') || outcomeA.includes('ineffective');
        const bPositive = outcomeB.includes('works') || outcomeB.includes('succeeds') || outcomeB.includes('effective');
        const bNegative = outcomeB.includes('fails') || outcomeB.includes('ineffective');

        const oppositeOutcomes = (aPositive && bNegative) || (aNegative && bPositive);

        if (oppositeOutcomes && conditionA !== conditionB) {
          return {
            hasContradiction: true,
            type: 'context_conflict',
            confidence: 0.85,
            reasoning: `same_strategy_opposite_outcomes: ${strategyA} in ${conditionA} vs ${conditionB} markets`
          };
        }
      }
    }

    // Additional check: Look for explicit context indicators in both claims
    // Pattern: "X works in Y" vs "X fails in Z" (more general)
    const generalContextPattern = /(.+?)\s+(works|fails|succeeds|is effective|is ineffective)\s+in\s+(\w+(?:\s+\w+)?)/i;
    const generalMatchA = claimAText.match(generalContextPattern);
    const generalMatchB = claimBText.match(generalContextPattern);

    if (generalMatchA && generalMatchB) {
      const subjectA = generalMatchA[1].trim().toLowerCase();
      const subjectB = generalMatchB[1].trim().toLowerCase();
      const outcomeA = generalMatchA[2].toLowerCase();
      const outcomeB = generalMatchB[2].toLowerCase();
      const contextA = generalMatchA[3].trim().toLowerCase();
      const contextB = generalMatchB[3].trim().toLowerCase();

      // Check if same subject with opposite outcomes in different contexts
      if (subjectA === subjectB && contextA !== contextB) {
        // Check for opposite outcomes in EITHER direction
        const aPositive = outcomeA.includes('works') || outcomeA.includes('succeeds') || outcomeA.includes('effective');
        const aNegative = outcomeA.includes('fails') || outcomeA.includes('ineffective');
        const bPositive = outcomeB.includes('works') || outcomeB.includes('succeeds') || outcomeB.includes('effective');
        const bNegative = outcomeB.includes('fails') || outcomeB.includes('ineffective');

        const oppositeOutcomes = (aPositive && bNegative) || (aNegative && bPositive);

        if (oppositeOutcomes) {
          return {
            hasContradiction: true,
            type: 'context_conflict',
            confidence: 0.85,
            reasoning: `same_subject_opposite_outcomes: ${subjectA} in ${contextA} vs ${contextB}`
          };
        }
      }
    }

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
    const isCausalA = claimA.artifactType === 'causal_claim' || claimA.artifactType === 'causal';
    const isCausalB = claimB.artifactType === 'causal_claim' || claimB.artifactType === 'causal';

    if (isCausalA && isCausalB) {
      const causeA = this.extractCause(claimA.claim);
      const causeB = this.extractCause(claimB.claim);
      const effectA = this.extractEffect(claimA.claim);
      const effectB = this.extractEffect(claimB.claim);

      // Reverse causality: A causes B vs B causes A
      if (causeA && effectA && causeB && effectB) {
        // Check if they're reverse causations
        if ((causeA.toLowerCase() === effectB.toLowerCase()) &&
            (effectA.toLowerCase() === causeB.toLowerCase())) {
          return {
            hasContradiction: true,
            type: 'causal_disagreement',
            confidence: 0.75,
            reasoning: `reverse_causality: ${causeA} → ${effectA} vs ${causeB} → ${effectB}`
          };
        }

        // Same cause, different effects
        if (causeA.toLowerCase() === causeB.toLowerCase() && effectA.toLowerCase() !== effectB.toLowerCase()) {
          return {
            hasContradiction: true,
            type: 'causal_disagreement',
            confidence: 0.75,
            reasoning: `same_cause_different_effects: ${causeA} → ${effectA} vs ${effectB}`
          };
        }
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
    const claimAText = claimA.claim.toLowerCase();
    const claimBText = claimB.claim.toLowerCase();

    // Check for recommendation patterns: "always X" vs "never X" or "don't X"
    const alwaysPatternA = claimAText.match(/always\s+(.+)/i);
    const neverPatternB = claimBText.match(/never\s+(.+)/i);
    const dontPatternB = claimBText.match(/don'?t\s+(.+)/i);

    if (alwaysPatternA && (neverPatternB || dontPatternB)) {
      const actionA = alwaysPatternA[1].trim();
      const actionB = (neverPatternB || dontPatternB)![1].trim();

      // Extract core action (first 2 words) to handle modifiers like "at 2%" or "in trending markets"
      const coreActionA = actionA.split(/\s+/).slice(0, 2).join(' ');
      const coreActionB = actionB.split(/\s+/).slice(0, 2).join(' ');

      // Check if they're talking about the same action
      if (coreActionA === coreActionB || actionA === actionB || actionA.includes(actionB) || actionB.includes(actionA)) {
        return {
          hasContradiction: true,
          type: 'recommendation_conflict',
          confidence: 0.8,
          reasoning: `opposite_recommendations: always ${actionA} vs never ${actionB}`
        };
      }
    }

    // Also check the other way
    const alwaysPatternB = claimBText.match(/always\s+(.+)/i);
    const neverPatternA = claimAText.match(/never\s+(.+)/i);
    const dontPatternA = claimAText.match(/don'?t\s+(.+)/i);

    if (alwaysPatternB && (neverPatternA || dontPatternA)) {
      const actionB = alwaysPatternB[1].trim();
      const actionA = (neverPatternA || dontPatternA)![1].trim();

      // Extract core action (first 2 words) to handle modifiers
      const coreActionA = actionA.split(/\s+/).slice(0, 2).join(' ');
      const coreActionB = actionB.split(/\s+/).slice(0, 2).join(' ');

      if (coreActionA === coreActionB || actionA === actionB || actionA.includes(actionB) || actionB.includes(actionA)) {
        return {
          hasContradiction: true,
          type: 'recommendation_conflict',
          confidence: 0.8,
          reasoning: `opposite_recommendations: always ${actionB} vs never ${actionA}`
        };
      }
    }

    // Check if both are recommendations with opposite approaches
    const isRecommendationA = claimA.artifactType === 'recommendation' || claimAText.includes('should') || claimAText.includes('recommend');
    const isRecommendationB = claimB.artifactType === 'recommendation' || claimBText.includes('should') || claimBText.includes('recommend');

    if (isRecommendationA && isRecommendationB) {
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
   * Find common terms across multiple claims
   */
  private findCommonTerms(claims: string[]): string[] {
    if (claims.length === 0) return [];

    // Extract words from first claim
    const firstWords = new Set(claims[0].split(/\s+/).filter(w => w.length > 3));
    const common: string[] = [];

    // Check which words appear in all claims
    for (const word of firstWords) {
      const inAll = claims.every(c => c.includes(word));
      if (inAll) {
        common.push(word);
      }
    }

    return common;
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
      /(\w+(?:\s+\w+)?)\s+(causes?|caused|resulted in|led to)/i,  // "X causes/caused Y" or "X resulted in Y"
      /due to\s+(\w+(?:\s+\w+)?)/i,
      /because of\s+(\w+(?:\s+\w+)?)/i
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
      /causes?\s+(\w+(?:\s+\w+)?)/i,  // "causes/cause X" (present tense)
      /caused\s+(\w+(?:\s+\w+)?)/i,    // "caused X" (past tense)
      /resulted in\s+(\w+(?:\s+\w+)?)/i,
      /led to\s+(\w+(?:\s+\w+)?)/i
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
  /**
   * Group claims by topic based on content similarity
   */
  clusterByTopic(artifacts: EpistemicArtifact[]): Map<string, EpistemicArtifact[]> {
    const clusters = new Map<string, EpistemicArtifact[]>();

    for (const artifact of artifacts) {
      // Extract topic from claim text
      let topic = this.extractTopic(artifact.artifactId);
      if (!topic) {
        topic = this.extractSubject(artifact.claim);
      }

      if (!topic) {
        topic = 'general';
      }

      if (!clusters.has(topic)) {
        clusters.set(topic, []);
      }
      clusters.get(topic)!.push(artifact);
    }

    return clusters;
  }
}

/**
 * Export singleton instance factory
 */
/**
 * Export factory function for repository-backed service
 */
export function createContradictionAndPluralityManager(repository: ILayer12Repository): ContradictionAndPluralityManager {
  return new ContradictionAndPluralityManager(repository);
}
