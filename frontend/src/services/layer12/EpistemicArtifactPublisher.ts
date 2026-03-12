/**
 * Layer 12: Collective Intelligence Exchange
 * EpistemicArtifactPublisher Service
 *
 * Converts internal insights and patterns into federatable epistemic artifacts.
 * Handles redaction, validation, and publication to the federation.
 */

import { v4 as uuidv4 } from 'uuid';
import type {
  EpistemicArtifact,
  ArtifactType,
  ArtifactContext,
  EvidenceEnvelope,
  ClaimProvenance,
  AllowedUse,
  PublicationOptions,
  PublicationResult,
  ValidationResult,
  PublishedInsight,
  Pattern,
  RedactedArtifact
} from '@/types/layer12/epistemic';

/**
 * Maps Layer 4 insight types to Layer 12 artifact types
 */
const INSIGHT_TO_ARTIFACT_MAP: Record<string, ArtifactType> = {
  'strategic_insight': 'recommendation',
  'reusable_playbook': 'recommendation',
  'validated_finding': 'observation',
  'architecture_decision': 'recommendation',
  'best_practice': 'pattern_claim',
  'risk_pattern': 'pattern_claim',
  'execution_lesson': 'observation',
  'research_summary': 'observation'
};

/**
 * Redaction patterns for local references
 */
const REDACTION_PATTERNS = [
  // Node IDs
  /\bnode-[a-z0-9-]+/gi,
  // Local file paths
  /\/[a-z0-9_\-\/]+\/local\//gi,
  // Local environment names
  /\blocal-(dev|staging|prod)-[a-z0-9]+\b/gi,
  // PII patterns (basic)
  /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, // email
  /\b\d{3}-\d{2}-\d{4}\b/g, // SSN
  /\b\d{16}\b/g, // Credit card
];

/**
 * Service for publishing epistemic artifacts to the federation
 */
export class EpistemicArtifactPublisher {
  private localNodeId: string;
  private publicationCache: Map<string, number> = new Map();
  private readonly DEFAULT_RATE_LIMIT = 50; // per day

  constructor(localNodeId: string) {
    this.localNodeId = localNodeId;
  }

  /**
   * Main entry point: Convert and publish an insight as a federatable artifact
   */
  async publishArtifact(
    insight: PublishedInsight | Pattern,
    options: PublicationOptions
  ): Promise<PublicationResult> {
    // Convert to artifact
    const artifact = await this.fromInsight(insight, options);

    // Validate for publication
    const validation = await this.validateForPublication(artifact);
    if (!validation.valid) {
      return {
        artifactId: artifact.artifactId,
        status: 'rejected',
        warnings: validation.warnings
      };
    }

    // Redact for federation
    const redacted = await this.redactForFederation(artifact);

    // Check rate limit
    if (!await this.checkRateLimit()) {
      throw new Error('Rate limit exceeded for publication');
    }

    // Publish to federation
    await this.publishToFederation(redacted);

    return {
      artifactId: artifact.artifactId,
      status: 'published',
      redactions: redacted.redactions,
      warnings: validation.warnings,
      publishedAt: Date.now()
    };
  }

  /**
   * Convert a Layer 4 insight into a Layer 12 epistemic artifact
   */
  async fromInsight(
    insight: PublishedInsight | Pattern,
    options: PublicationOptions
  ): Promise<EpistemicArtifact> {
    const artifactId = `artifact_${uuidv4()}`;
    const artifactType = INSIGHT_TO_ARTIFACT_MAP[insight.type] || 'observation';

    // Extract context from insight
    const context = this.extractContext(insight);

    // Extract evidence from insight
    const evidence = this.extractEvidence(insight);

    // Build artifact
    const artifact: EpistemicArtifact = {
      artifactId,
      artifactType,
      originNode: this.localNodeId,
      originLayer: 4,
      createdAt: insight.publishedAt || Date.now(),
      version: '1.0.0',
      claim: insight.summary || insight.title,
      summary: insight.description || insight.content?.substring(0, 500) || '',
      context,
      evidence,
      limitations: insight.limitations || [],
      allowedUses: options.allowedUses,
      contradictions: options.contradictions,
      provenance: {
        sourceArtifacts: insight.sourceArtifacts || [],
        sourceInsights: [insight.insightId],
        lineageDepth: 1,
        createdBy: insight.createdBy || 'system',
        creationPath: [`insight_${insight.insightId}`]
      }
    };

    return artifact;
  }

  /**
   * Extract context metadata from an insight
   */
  private extractContext(insight: PublishedInsight | Pattern): ArtifactContext {
    const context: ArtifactContext = {};

    // Extract domain from insight metadata or tags
    if (insight.domain) context.domain = insight.domain;
    else if (insight.tags?.includes('financial')) context.domain = 'financial_planning';
    else if (insight.tags?.includes('healthcare')) context.domain = 'healthcare';
    else if (insight.tags?.includes('compliance')) context.domain = 'compliance';

    // Extract mission type
    if (insight.missionType) context.missionType = insight.missionType;

    // Extract agent topology
    if (insight.agentTopology) context.agentTopology = insight.agentTopology;
    else if (insight.metadata?.agentTopology) context.agentTopology = insight.metadata.agentTopology;

    // Extract policy regime
    if (insight.policyRegime) context.policyRegime = insight.policyRegime;
    else if (insight.metadata?.policyRegime) context.policyRegime = insight.metadata.policyRegime;

    // Extract environment class
    if (insight.environmentClass) context.environmentClass = insight.environmentClass;
    else if (insight.metadata?.environmentClass) context.environmentClass = insight.metadata.environmentClass;

    // Extract constraints
    if (insight.constraints?.length) context.constraints = insight.constraints;
    else if (insight.metadata?.constraints) context.constraints = insight.metadata.constraints;

    // Extract regulatory environment
    if (insight.regulatoryEnvironment) context.regulatoryEnvironment = insight.regulatoryEnvironment;

    // Extract model family if relevant
    if (insight.modelFamily) context.modelFamily = insight.modelFamily;
    else if (insight.metadata?.modelFamily) context.modelFamily = insight.metadata.modelFamily;

    return context;
  }

  /**
   * Extract evidence envelope from an insight
   */
  private extractEvidence(insight: PublishedInsight | Pattern): EvidenceEnvelope {
    const evidence: EvidenceEnvelope = {
      confidence: insight.confidence ?? 0.7
    };

    // Extract sample size
    if (insight.sampleSize) evidence.sampleSize = insight.sampleSize;
    else if (insight.metadata?.sampleSize) evidence.sampleSize = insight.metadata.sampleSize;

    // Extract effect size
    if (insight.effectSize) evidence.effectSize = insight.effectSize;
    else if (insight.metadata?.effectSize) evidence.effectSize = insight.metadata.effectSize;

    // Extract validation method
    if (insight.validationMethod) evidence.validationMethod = insight.validationMethod;
    else if (insight.metadata?.validationMethod) evidence.validationMethod = insight.metadata.validationMethod;

    // Extract stability score
    if (insight.stabilityScore) evidence.stabilityScore = insight.stabilityScore;
    else if (insight.metadata?.stabilityScore) evidence.stabilityScore = insight.metadata.stabilityScore;

    // Extract reproducibility
    if (insight.reproducibility) evidence.reproducibility = insight.reproducibility;
    else if (insight.metadata?.reproducibility) evidence.reproducibility = insight.metadata.reproducibility;

    // Extract supporting artifacts
    if (insight.supportingArtifacts?.length) evidence.supportingArtifacts = insight.supportingArtifacts;

    // Extract time span if available
    if (insight.timeSpan) evidence.timeSpan = insight.timeSpan;
    else if (insight.metadata?.timeSpan) evidence.timeSpan = insight.metadata.timeSpan;

    return evidence;
  }

  /**
   * Validate an artifact meets publication standards
   */
  async validateForPublication(artifact: EpistemicArtifact): Promise<ValidationResult> {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Required fields
    if (!artifact.context?.domain) {
      errors.push('missing_context_domain');
    }

    if (!artifact.evidence || artifact.evidence.confidence < 0.5) {
      errors.push('low_confidence');
    }

    if (!artifact.provenance?.sourceInsights?.length) {
      errors.push('missing_provenance');
    }

    if (!artifact.allowedUses?.length) {
      errors.push('missing_allowed_uses');
    }

    // Warnings
    if (artifact.evidence.confidence < 0.7) {
      warnings.push('moderate_confidence');
    }

    if (artifact.evidence.sampleSize && artifact.evidence.sampleSize < 10) {
      warnings.push('small_sample_size');
    }

    if (artifact.limitations?.length === 0) {
      warnings.push('no_limitations_declared');
    }

    // Check for transferability
    if (artifact.context.domain && artifact.context.agentTopology) {
      // Domain-specific topologies have lower transferability
      warnings.push('context_specific_artifact');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Redact local references and sensitive data before federation
   */
  async redactForFederation(artifact: EpistemicArtifact): Promise<RedactedArtifact> {
    const redactions: string[] = [];
    let claim = artifact.claim;
    let summary = artifact.summary;

    // Apply redaction patterns
    for (const pattern of REDACTION_PATTERNS) {
      const claimMatches = claim.match(pattern);
      const summaryMatches = summary.match(pattern);

      if (claimMatches) {
        claim = claim.replace(pattern, '[REDACTED]');
        redactions.push(`claim: ${pattern.source}`);
      }

      if (summaryMatches) {
        summary = summary.replace(pattern, '[REDACTED]');
        redactions.push(`summary: ${pattern.source}`);
      }
    }

    // Redact local node references in context
    const context = { ...artifact.context };
    if (context.agentTopology?.includes(this.localNodeId)) {
      context.agentTopology = context.agentTopology.replace(this.localNodeId, '[THIS_NODE]');
      redactions.push('context: node_id');
    }

    // Redact local file paths
    if (context.constraints) {
      context.constraints = context.constraints.map(c =>
        c.replace(/\/[a-z0-9_\-\/]+\/local\//gi, '/[LOCAL_PATH]/')
      );
      redactions.push('context: local_paths');
    }

    return {
      ...artifact,
      claim,
      summary,
      context,
      redactions
    };
  }

  /**
   * Check if insight is eligible for federation
   */
  isFederatable(insight: PublishedInsight | Pattern): boolean {
    // Must have minimum confidence
    if ((insight.confidence ?? 0) < 0.7) return false;

    // Must have domain context
    if (!insight.domain && !insight.tags?.length) return false;

    // Must not be marked as private
    if (insight.private || insight.sensitive) return false;

    // Must have proper provenance
    if (!insight.insightId) return false;

    return true;
  }

  /**
   * Check publication rate limit
   */
  private async checkRateLimit(): Promise<boolean> {
    const today = new Date().toISOString().split('T')[0];
    const cacheKey = `${this.localNodeId}_${today}`;
    const currentCount = this.publicationCache.get(cacheKey) || 0;

    if (currentCount >= this.DEFAULT_RATE_LIMIT) {
      return false;
    }

    this.publicationCache.set(cacheKey, currentCount + 1);
    return true;
  }

  /**
   * Publish artifact to federation (L11 fabric)
   */
  private async publishToFederation(artifact: RedactedArtifact): Promise<void> {
    // This will integrate with Layer 11 Distributed Fabric
    // For now, we store locally and mark for federation
    await this.storeArtifact(artifact);
    await this.markForFederation(artifact.artifactId);
  }

  /**
   * Store artifact in local registry
   */
  private async storeArtifact(artifact: RedactedArtifact): Promise<void> {
    // TODO: Integrate with database layer
    // For now, this is a placeholder
    console.log(`[L12] Storing artifact: ${artifact.artifactId}`);
  }

  /**
   * Mark artifact for federation via L11
   */
  private async markForFederation(artifactId: string): Promise<void> {
    // TODO: Integrate with Layer 11 fabric
    console.log(`[L12] Marking for federation: ${artifactId}`);
  }
}

/**
 * Layer 4 PublishedInsight interface (simplified for reference)
 */
interface PublishedInsight {
  insightId: string;
  type: string;
  title: string;
  summary?: string;
  description?: string;
  content?: string;
  confidence?: number;
  publishedAt: number;
  createdBy?: string;
  domain?: string;
  missionType?: string;
  agentTopology?: string;
  policyRegime?: string;
  environmentClass?: string;
  constraints?: string[];
  regulatoryEnvironment?: string;
  modelFamily?: string;
  tags?: string[];
  private?: boolean;
  sensitive?: boolean;
  limitations?: string[];
  sampleSize?: number;
  effectSize?: number;
  validationMethod?: string;
  stabilityScore?: number;
  reproducibility?: number;
  supportingArtifacts?: string[];
  timeSpan?: { start: number; end: number };
  sourceArtifacts?: string[];
  metadata?: Record<string, unknown>;
}

/**
 * Layer 4 Pattern interface (simplified)
 */
interface Pattern {
  patternId: string;
  type: string;
  title: string;
  description?: string;
  content?: string;
  summary?: string;
  confidence?: number;
  createdAt: number;
  createdBy?: string;
  domain?: string;
  tags?: string[];
  private?: boolean;
  limitations?: string[];
  sampleSize?: number;
  evidence?: {
    sampleSize?: number;
    confidence: number;
    effectSize?: number;
    validationMethod?: string;
    stabilityScore?: number;
    reproducibility?: number;
  };
  sourceArtifacts?: string[];
  metadata?: Record<string, unknown>;
}

/**
 * Redacted artifact - artifact after redaction
 */
interface RedactedArtifact extends EpistemicArtifact {
  redactions: string[];
}

/**
 * Export singleton instance factory
 */
export function createEpistemicArtifactPublisher(localNodeId: string): EpistemicArtifactPublisher {
  return new EpistemicArtifactPublisher(localNodeId);
}
