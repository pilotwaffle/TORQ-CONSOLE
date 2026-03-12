/**
 * Layer 12: Collective Intelligence Exchange
 * LocalQualificationEngine Service
 *
 * Evaluates incoming claims locally before adoption.
 * Each receiving node runs this to determine:
 * - Can this claim be used here?
 * - How should it be used?
 * - What warnings apply?
 */

import type {
  EpistemicArtifact,
  ArtifactContext,
  LocalContext,
  QualificationResult,
  ContextComparison,
  TransferabilityCheck,
  PolicyCompatibility,
  AllowedUse,
  SuggestedAction
} from '@/types/layer12/epistemic';

/**
 * Configuration for qualification thresholds
 */
interface QualificationConfig {
  relevanceThresholds: {
    advisory: number;
    simulationRequired: number;
    ignore: number;
  };
  trustThresholds: {
    low: number;
    medium: number;
    high: number;
  };
  contextMatchWeights: {
    domain: number;
    missionType: number;
    agentTopology: number;
    environment: number;
  };
}

/**
 * Default qualification configuration
 */
const DEFAULT_CONFIG: QualificationConfig = {
  relevanceThresholds: {
    advisory: 0.5,
    simulationRequired: 0.3,
    ignore: 0.2
  },
  trustThresholds: {
    low: 0.3,
    medium: 0.6,
    high: 0.8
  },
  contextMatchWeights: {
    domain: 0.4,
    missionType: 0.3,
    agentTopology: 0.2,
    environment: 0.1
  }
};

/**
 * Service for local qualification of incoming artifacts
 */
export class LocalQualificationEngine {
  private config: QualificationConfig;
  private localNodePolicies: Map<string, string[]> = new Map(); // domain -> policy IDs

  constructor(config?: Partial<QualificationConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Main entry point: Qualify an artifact for local adoption
   */
  async qualifyArtifact(
    artifact: EpistemicArtifact,
    localContext: LocalContext
  ): Promise<QualificationResult> {
    // 1. Check transferability
    const transferability = await this.checkTransferability(artifact, localContext);

    // 2. Compare contexts
    const contextComparison = this.compareContexts(artifact.context, localContext);

    // 3. Check policy compatibility
    const policyCompatibility = await this.checkPolicyCompatibility(artifact, localContext);

    // 4. Compute local relevance
    const localRelevance = this.computeRelevance(artifact, localContext);

    // 5. Compute local trust
    const localTrust = await this.computeTrust(artifact, localContext);

    // 6. Compute provenance strength
    const provenanceStrength = this.computeProvenanceStrength(artifact);

    // 7. Compute confidence stability
    const confidenceStability = this.computeConfidenceStability(artifact);

    // 8. Determine classification
    const category = this.determineCategory(
      artifact,
      transferability,
      policyCompatibility,
      localRelevance,
      localTrust
    );

    // 9. Generate warnings
    const warnings = this.generateWarnings(
      artifact,
      transferability,
      contextComparison,
      policyCompatibility
    );

    // 10. Suggest action (internal call with parameters)
    const suggestedAction = this.suggestActionInternal(
      category,
      localRelevance,
      localTrust,
      transferability,
      warnings
    );

    // 11. Determine recommended uses
    const recommendedUses = this.determineRecommendedUses(artifact, category, localTrust);

    return {
      artifactId: artifact.artifactId,
      category,
      localRelevance,
      provenanceStrength,
      confidenceStability,
      overallTrust: localTrust,
      hasContextClash: contextComparison.overallMatch < 0.3,
      hasContradictions: (artifact.contradictions?.length || 0) > 0,
      requiresSimulation: suggestedAction === 'send_to_simulation',
      policyCompatible: policyCompatibility.requiresApproval === false,
      contextComparison,
      recommendedUses,
      warnings,
      suggestedAction
    };
  }

  /**
   * Check if artifact can transfer across nodes
   */
  async checkTransferability(
    artifact: EpistemicArtifact,
    localContext: LocalContext
  ): Promise<TransferabilityCheck> {
    const reasons: string[] = [];
    const requiredContext: string[] = [];
    let canMove = true;
    let riskLevel: 'low' | 'medium' | 'high' = 'low';
    let requiresAdaptation = false;

    // Check domain match
    if (artifact.context.domain && artifact.context.domain !== localContext.domain) {
      canMove = false;
      riskLevel = 'high';
      reasons.push('domain_mismatch');
      requiredContext.push(`domain_${artifact.context.domain}`);
    }

    // Check regulatory environment
    if (artifact.context.regulatoryEnvironment && localContext.policyRegime) {
      if (artifact.context.regulatoryEnvironment !== localContext.policyRegime) {
        requiresAdaptation = true;
        riskLevel = riskLevel === 'low' ? 'medium' : riskLevel;
        reasons.push('regulatory_difference');
      }
    }

    // Check environment class
    if (artifact.context.environmentClass && artifact.context.environmentClass !== localContext.environmentClass) {
      requiresAdaptation = true;
      reasons.push('environment_difference');
    }

    // Check confidence level
    if (artifact.evidence.confidence < 0.7) {
      riskLevel = riskLevel === 'low' ? 'medium' : 'high';
      reasons.push('low_confidence');
    }

    // Check sample size
    if (artifact.evidence.sampleSize && artifact.evidence.sampleSize < 20) {
      riskLevel = riskLevel === 'low' ? 'medium' : riskLevel;
      reasons.push('small_sample');
    }

    return {
      canMoveAcrossNodes: canMove,
      transferable: canMove, // Alias for compatibility
      requiresContext: requiredContext,
      localAdaptationRequired: requiresAdaptation,
      riskLevel,
      reasons,
      score: canMove ? 1.0 - (reasons.length * 0.1) : 0.0 // Computed transferability score
    };
  }

  /**
   * Compare artifact context to local context
   */
  compareContexts(
    artifactContext: ArtifactContext,
    localContext: LocalContext
  ): ContextComparison {
    let matches = 0;
    let total = 0;

    // Domain match
    total += 1;
    const domainMatch = artifactContext.domain === localContext.domain;
    if (domainMatch) matches += 1;

    // Mission type match
    if (artifactContext.missionType && localContext.missionType) {
      total += 1;
      const missionTypeMatch = artifactContext.missionType === localContext.missionType;
      if (missionTypeMatch) matches += 1;
    }

    // Agent topology match
    if (artifactContext.agentTopology && localContext.agentTopology) {
      total += 1;
      const agentTopologyMatch = artifactContext.agentTopology === localContext.agentTopology;
      if (agentTopologyMatch) matches += 1;
    }

    // Environment match
    if (artifactContext.environmentClass && localContext.environmentClass) {
      total += 1;
      const environmentMatch = artifactContext.environmentClass === localContext.environmentClass;
      if (environmentMatch) matches += 1;
    }

    const overallMatch = total > 0 ? matches / total : 0;

    return {
      domainMatch,
      missionTypeMatch: artifactContext.missionType === localContext.missionType,
      agentTopologyMatch: artifactContext.agentTopology === localContext.agentTopology,
      environmentMatch: artifactContext.environmentClass === localContext.environmentClass,
      overallMatch
    };
  }

  /**
   * Check policy compatibility
   */
  async checkPolicyCompatibility(
    artifact: EpistemicArtifact,
    localContext: LocalContext
  ): Promise<PolicyCompatibility> {
    const compatibleWith: string[] = [];
    const conflictsWith: string[] = [];
    let requiresApproval = false;
    let authorityLevel: 'node' | 'region' | 'network' = 'node';

    // Get local policies for this domain
    const localPolicies = localContext.policies || localContext.activePolicies || [];
    const domainPolicies = this.localNodePolicies.get(localContext.domain) || [];

    // Check for minimum confidence policy
    const minConfidencePolicy = localPolicies.find(p => p.startsWith('min-confidence-'));
    if (minConfidencePolicy) {
      const minConfidence = parseFloat(minConfidencePolicy.split('-')[2]);
      if (artifact.evidence.confidence < minConfidence) {
        conflictsWith.push('minimum_confidence_not_met');
        requiresApproval = true;
      }
    }

    // Check for conflicts
    if (artifact.context.policyRegime) {
      if (!localPolicies.includes(artifact.context.policyRegime)) {
        conflictsWith.push(artifact.context.policyRegime);
        requiresApproval = true;
        authorityLevel = 'region';
      } else {
        compatibleWith.push(artifact.context.policyRegime);
      }
    }

    // Check domain-level policies
    for (const policy of domainPolicies) {
      if (localPolicies.includes(policy)) {
        compatibleWith.push(policy);
      } else {
        conflictsWith.push(policy);
        requiresApproval = true;
      }
    }

    // Check allowed uses for allocative eligibility - requires higher authority
    if (artifact.allowedUses.includes('allocative_eligible')) {
      // If allocative_eligible is in allowed uses but not in local context permissions
      if (!localPolicies.includes('allocative-requires-simulation')) {
        conflictsWith.push('allowed_use_restriction');
      }
      requiresApproval = true;
      authorityLevel = 'network';
    }

    return {
      compatibleWith,
      conflictsWith,
      violations: conflictsWith, // Alias
      requiresApproval,
      authorityLevel,
      compatible: conflictsWith.length === 0 && !requiresApproval
    };
  }

  /**
   * Compute local relevance score (0-1)
   */
  computeRelevance(
    artifact: EpistemicArtifact,
    localContext: LocalContext
  ): number {
    let relevance = 0;
    const weights = this.config.contextMatchWeights;

    // Domain match (highest weight)
    if (artifact.context.domain && artifact.context.domain === localContext.domain) {
      relevance += weights.domain;
    }

    // Mission type match
    if (artifact.context.missionType && artifact.context.missionType === localContext.missionType) {
      relevance += weights.missionType;
    }

    // Agent topology match
    if (artifact.context.agentTopology && artifact.context.agentTopology === localContext.agentTopology) {
      relevance += weights.agentTopology;
    }

    // Environment match
    if (artifact.context.environmentClass && artifact.context.environmentClass === localContext.environmentClass) {
      relevance += weights.environment;
    }

    return Math.min(1, relevance);
  }

  /**
   * Compute local trust score (0-1)
   */
  async computeTrust(
    artifact: EpistemicArtifact,
    localContext: LocalContext
  ): Promise<number> {
    let trust = 0.0;

    // Evidence confidence (primary factor) - higher weight for very high confidence
    if (artifact.evidence.confidence >= 0.9) {
      trust += artifact.evidence.confidence * 0.4; // Higher weight for exceptional confidence
    } else {
      trust += artifact.evidence.confidence * 0.35;
    }

    // Stability score
    if (artifact.evidence.stabilityScore) {
      trust += artifact.evidence.stabilityScore * 0.15;
    }

    // Provenance strength (based on lineage depth and sources)
    const provenanceStrength = this.computeProvenanceStrength(artifact);
    trust += provenanceStrength * 0.25;

    // Sample size (more evidence = higher trust)
    if (artifact.evidence.sampleSize) {
      const sampleBonus = Math.min(0.15, artifact.evidence.sampleSize / 5000);
      trust += sampleBonus;
    }

    // Number of sources increases trust
    if (artifact.evidence.sources?.length) {
      trust += Math.min(0.1, artifact.evidence.sources.length * 0.03);
    }

    // Deduction for limitations
    if (artifact.limitations?.length) {
      const limitationPenalty = Math.min(0.15, artifact.limitations.length * 0.05);
      trust -= limitationPenalty;
    }

    // Deduction for contradictions
    if (artifact.contradictions?.length) {
      trust -= 0.1 * artifact.contradictions.length;
    }

    return Math.max(0, Math.min(1, trust));
  }

  /**
   * Compute trust score with detailed breakdown
   * Returns an object with overall trust and component scores
   */
  async computeTrustScore(
    artifact: EpistemicArtifact,
    localContext: LocalContext
  ): Promise<{
    overall: number;
    provenanceStrength: number;
    confidenceStability: number;
  }> {
    const overall = await this.computeTrust(artifact, localContext);
    const provenanceStrength = this.computeProvenanceStrength(artifact);
    const confidenceStability = this.computeConfidenceStability(artifact);

    return { overall, provenanceStrength, confidenceStability };
  }

  /**
   * Compute provenance strength (0-1)
   */
  computeProvenanceStrength(artifact: EpistemicArtifact): number {
    let strength = 0.5;

    // Verification level adds significant strength
    if (artifact.provenance.verificationLevel === 'verified') {
      strength += 0.25;
    } else if (artifact.provenance.verificationLevel === 'peer-reviewed') {
      strength += 0.35;
    }

    // Peer review count adds strength
    if (artifact.provenance.peerReviewCount) {
      strength += Math.min(0.15, artifact.provenance.peerReviewCount * 0.03);
    }

    // More source artifacts = stronger provenance
    if (artifact.provenance.sourceArtifacts?.length) {
      strength += Math.min(0.1, artifact.provenance.sourceArtifacts.length * 0.05);
    }

    // More source insights = stronger provenance
    if (artifact.provenance.sourceInsights?.length) {
      strength += Math.min(0.1, artifact.provenance.sourceInsights.length * 0.03);
    }

    // Deeper lineage = stronger (up to a point)
    if (artifact.provenance.lineageDepth > 1) {
      strength += Math.min(0.05, artifact.provenance.lineageDepth * 0.02);
    }

    return Math.min(1, strength);
  }

  /**
   * Compute confidence stability (0-1)
   */
  computeConfidenceStability(artifact: EpistemicArtifact): number {
    let stability = 0.5;

    // Large sample size increases stability
    if (artifact.evidence.sampleSize && artifact.evidence.sampleSize > 500) {
      stability += 0.1;
    }
    if (artifact.evidence.sampleSize && artifact.evidence.sampleSize > 5000) {
      stability += 0.1;
    }

    // Rigorous methodology increases stability
    if (artifact.evidence.methodology === 'peer-reviewed') {
      stability += 0.2;
    } else if (artifact.evidence.methodology === 'controlled-experiment') {
      stability += 0.25;
    } else if (artifact.evidence.methodology === 'statistical-analysis') {
      stability += 0.1;
    }

    // Multiple sources increase stability
    if (artifact.evidence.sources && artifact.evidence.sources.length >= 3) {
      stability += 0.1;
    }

    // Explicit stability score
    if (artifact.evidence.stabilityScore) {
      stability = (stability + artifact.evidence.stabilityScore) / 2;
    }

    // Reproducibility adds to stability
    if (artifact.evidence.reproducibility) {
      stability = (stability + artifact.evidence.reproducibility) / 2;
    }

    return Math.min(1, stability);
  }

  /**
   * Determine category for artifact
   */
  private determineCategory(
    artifact: EpistemicArtifact,
    transferability: TransferabilityCheck,
    policyCompatibility: PolicyCompatibility,
    localRelevance: number,
    localTrust: number
  ): QualificationResult['category'] {
    // Check allowed uses from artifact
    if (!artifact.allowedUses.includes('informational')) {
      // Artifact has stricter usage requirements
      if (artifact.allowedUses.includes('allocative_eligible')) {
        return 'allocative_eligible';
      }
      if (artifact.allowedUses.includes('simulation_only')) {
        return 'simulation_only';
      }
      if (artifact.allowedUses.includes('advisory')) {
        return 'advisory';
      }
    }

    // Determine based on qualification results
    if (localTrust < this.config.trustThresholds.low) {
      return 'informational';
    }

    if (localRelevance < this.config.relevanceThresholds.ignore) {
      return 'informational';
    }

    if (transferability.riskLevel === 'high') {
      return 'informational';
    }

    if (policyCompatibility.requiresApproval) {
      if (localTrust >= this.config.trustThresholds.high) {
        return 'advisory';
      }
      return 'informational';
    }

    if (localRelevance >= this.config.relevanceThresholds.advisory &&
        localTrust >= this.config.trustThresholds.medium) {
      // Check if simulation is required
      if (localRelevance < this.config.relevanceThresholds.simulationRequired) {
        return 'simulation_only';
      }
      return 'advisory';
    }

    return 'informational';
  }

  /**
   * Generate warnings based on qualification results
   */
  private generateWarnings(
    artifact: EpistemicArtifact,
    transferability: TransferabilityCheck,
    contextComparison: ContextComparison,
    policyCompatibility: PolicyCompatibility
  ): string[] {
    const warnings: string[] = [];

    // Transferability warnings
    if (transferability.riskLevel === 'high') {
      warnings.push('high_transferability_risk');
    }
    if (transferability.localAdaptationRequired) {
      warnings.push('local_adaptation_required');
    }

    // Context mismatch warnings
    if (!contextComparison.domainMatch) {
      warnings.push('domain_mismatch');
    }
    if (contextComparison.overallMatch < 0.3) {
      warnings.push('low_context_match');
    }

    // Policy conflict warnings
    if (policyCompatibility.conflictsWith.length > 0) {
      warnings.push(`policy_conflicts: ${policyCompatibility.conflictsWith.join(', ')}`);
    }

    // Evidence warnings
    if (artifact.evidence.confidence < 0.7) {
      warnings.push('moderate_confidence');
    }
    if (artifact.evidence.sampleSize && artifact.evidence.sampleSize < 20) {
      warnings.push('small_sample_size');
    }

    // Limitation warnings
    if (artifact.limitations?.length > 3) {
      warnings.push('multiple_limitations');
    }

    // Contradiction warnings
    if (artifact.contradictions?.length) {
      warnings.push(`has_${artifact.contradictions.length}_contradictions`);
    }

    return warnings;
  }

  /**
   * Suggest action based on qualification result
   * Public method that takes a QualificationResult
   */
  async suggestAction(result: QualificationResult): Promise<SuggestedAction> {
    // Extract the needed parameters from the result
    const { category, localRelevance, overallTrust: localTrust } = result;

    // Reconstruct transferability from context comparison
    const transferability: TransferabilityCheck = {
      transferable: !result.hasContextClash && result.policyCompatible,
      score: result.localRelevance,
      riskLevel: result.hasContextClash ? 'high' : result.warnings.length > 0 ? 'medium' : 'low',
      reasons: result.warnings,
      requiredContext: result.contextComparison.overallMatch < 0.5 ? [result.contextComparison] : []
    };

    return this.suggestActionInternal(category, localRelevance, localTrust, transferability, result.warnings);
  }

  /**
   * Suggest action based on qualification results
   * Internal method with full parameters
   */
  private suggestActionInternal(
    category: QualificationResult['category'],
    localRelevance: number,
    localTrust: number,
    transferability: TransferabilityCheck,
    warnings: string[]
  ): SuggestedAction {
    // High trust, high relevance -> use or simulate
    if (localTrust >= this.config.trustThresholds.high &&
        localRelevance >= this.config.relevanceThresholds.advisory) {
      if (transferability.riskLevel === 'medium' || warnings.length > 0) {
        return 'send_to_simulation';
      }
      return 'use_advisory';
    }

    // Low relevance -> ignore
    if (localRelevance < this.config.relevanceThresholds.ignore) {
      return 'ignore';
    }

    // Low trust -> informational only
    if (localTrust < this.config.trustThresholds.low) {
      return 'store_informational';
    }

    // Has contradictions -> governance review
    if (warnings.some(w => w.includes('contradiction'))) {
      return 'send_to_governance';
    }

    // Policy conflicts -> governance review
    if (warnings.some(w => w.includes('policy_conflict'))) {
      return 'send_to_governance';
    }

    // High transferability risk -> informational
    if (transferability.riskLevel === 'high') {
      return 'store_informational';
    }

    // Medium trust, medium relevance -> advisory
    if (localTrust >= this.config.trustThresholds.medium &&
        localRelevance >= this.config.relevanceThresholds.advisory) {
      return 'use_advisory';
    }

    // Default -> informational
    return 'store_informational';
  }

  /**
   * Determine recommended uses based on qualification
   */
  private determineRecommendedUses(
    artifact: EpistemicArtifact,
    category: QualificationResult['category'],
    localTrust: number
  ): AllowedUse[] {
    const uses: AllowedUse[] = [];

    // Start with informational
    uses.push('informational');

    // Advisory uses
    if (category === 'advisory' || category === 'simulation_only' || category === 'allocative_eligible') {
      if (artifact.allowedUses.includes('advisory')) {
        uses.push('advisory');
      }
    }

    // Simulation uses
    if (category === 'simulation_only' || category === 'allocative_eligible') {
      if (artifact.allowedUses.includes('simulation_only')) {
        uses.push('simulation_only');
      }
    }

    // Allocative uses (most restrictive)
    if (category === 'allocative_eligible' &&
        localTrust >= this.config.trustThresholds.high &&
        artifact.allowedUses.includes('allocative_eligible')) {
      uses.push('allocative_eligible');
    }

    return uses;
  }

  /**
   * Set local node policies for a domain
   */
  setLocalPolicies(domain: string, policyIds: string[]): void {
    this.localNodePolicies.set(domain, policyIds);
  }

  /**
   * Get local node policies for a domain
   */
  getLocalPolicies(domain: string): string[] {
    return this.localNodePolicies.get(domain) || [];
  }
}

/**
 * Export singleton instance factory
 */
export function createLocalQualificationEngine(
  config?: Partial<QualificationConfig>
): LocalQualificationEngine {
  return new LocalQualificationEngine(config);
}
