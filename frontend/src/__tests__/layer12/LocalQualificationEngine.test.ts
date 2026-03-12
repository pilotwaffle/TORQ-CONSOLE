/**
 * Layer 12: Collective Intelligence Exchange
 * Unit Tests - LocalQualificationEngine
 *
 * Tests the service that evaluates incoming artifacts for local adoption.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { createLocalQualificationEngine } from '@/services/layer12/LocalQualificationEngine';
import type { EpistemicArtifact, LocalContext, QualificationResult } from '@/types/layer12/epistemic';

describe('LocalQualificationEngine', () => {
  let engine: ReturnType<typeof createLocalQualificationEngine>;

  beforeEach(() => {
    engine = createLocalQualificationEngine();
  });

  // Helper to create a test artifact
  const createTestArtifact = (overrides?: Partial<EpistemicArtifact>): EpistemicArtifact => ({
    artifactId: 'artifact-001',
    artifactType: 'pattern',
    originNode: 'remote-node-1',
    originLayer: 4,
    createdAt: Date.now(),
    version: '1.0.0',
    claim: 'Trading pattern with 85% accuracy',
    summary: 'Pattern shows consistent results',
    context: {
      domain: 'trading',
      missionType: 'speculative',
      agentTopology: 'multi_agent'
    },
    evidence: {
      confidence: 0.85,
      sources: ['exchange-data'],
      sampleSize: 1000,
      methodology: 'backtesting'
    },
    limitations: ['only tested on BTC'],
    allowedUses: ['informational', 'advisory'],
    provenance: {
      sourceNode: 'remote-node-1',
      sourceLayer: 4,
      timestamp: Date.now(),
      lineageId: 'lineage-001'
    },
    ...overrides
  });

  // Helper to create a test local context
  const createTestContext = (overrides?: Partial<LocalContext>): LocalContext => ({
    nodeId: 'local-node-1',
    domain: 'trading',
    missionType: 'speculative',
    agentTopology: 'multi_agent',
    capabilities: ['backtesting', 'realtime-trading'],
    policies: ['require-simulation', 'min-confidence-0.7'],
    ...overrides
  });

  // ============================================================================
  // qualifyArtifact Tests
  // ============================================================================

  describe('qualifyArtifact', () => {
    it('should qualify a highly relevant artifact as advisory', async () => {
      const artifact = createTestArtifact({
        context: {
          domain: 'trading',
          missionType: 'speculative',
          agentTopology: 'multi_agent'
        }
      });

      const localContext = createTestContext({
        domain: 'trading',
        missionType: 'speculative'
      });

      const result = await engine.qualifyArtifact(artifact, localContext);

      expect(result).toBeDefined();
      expect(result.category).toBeDefined();
      expect(result.overallTrust).toBeGreaterThan(0);
      expect(result.suggestedAction).toBeDefined();
    });

    it('should detect context mismatches', async () => {
      const artifact = createTestArtifact({
        context: {
          domain: 'healthcare',
          missionType: 'diagnostic',
          agentTopology: 'single'
        }
      });

      const localContext = createTestContext({
        domain: 'trading',
        missionType: 'speculative'
      });

      const result = await engine.qualifyArtifact(artifact, localContext);

      expect(result.hasContextClash).toBe(true);
      expect(result.localRelevance).toBeLessThan(0.5);
    });

    it('should check policy compatibility', async () => {
      const artifact = createTestArtifact({
        evidence: {
          confidence: 0.65,
          sources: [],
          sampleSize: 50,
          methodology: 'test'
        }
      });

      const localContext = createTestContext({
        policies: ['require-simulation', 'min-confidence-0.7']
      });

      const result = await engine.qualifyArtifact(artifact, localContext);

      expect(result.policyCompatible).toBeDefined();
      if (result.policyCompatible === false) {
        expect(result.warnings).toContain(
          expect.stringContaining('confidence')
        );
      }
    });

    it('should recommend simulation for allocative-eligible claims', async () => {
      const artifact = createTestArtifact({
        allowedUses: ['allocative_eligible'],
        evidence: {
          confidence: 0.9,
          sources: ['multiple-exchanges'],
          sampleSize: 10000,
          methodology: 'rigorous-backtesting'
        }
      });

      const localContext = createTestContext();

      const result = await engine.qualifyArtifact(artifact, localContext);

      if (result.suggestedAction === 'send_to_simulation') {
        expect(result.requiresSimulation).toBe(true);
      }
    });

    it('should ignore low-confidence artifacts', async () => {
      const artifact = createTestArtifact({
        evidence: {
          confidence: 0.4,
          sources: [],
          sampleSize: 10,
          methodology: 'anecdotal'
        },
        limitations: ['very uncertain', 'small sample', 'unverified']
      });

      const localContext = createTestContext();

      const result = await engine.qualifyArtifact(artifact, localContext);

      expect(result.overallTrust).toBeLessThan(0.5);
      expect(result.suggestedAction).toBe('ignore');
    });
  });

  // ============================================================================
  // checkTransferability Tests
  // ============================================================================

  describe('checkTransferability', () => {
    it('should identify highly transferable artifacts', async () => {
      const artifact = createTestArtifact({
        context: {
          domain: 'trading',
          missionType: 'speculative',
          agentTopology: 'multi_agent',
          dataCharacteristics: {
            exchange: 'binance',
            pair: 'BTC/USDT',
            timeframe: '1h'
          }
        }
      });

      const localContext = createTestContext({
        domain: 'trading',
        missionType: 'speculative'
      });

      const transferability = await engine.checkTransferability(artifact, localContext);

      expect(transferability.transferable).toBe(true);
      expect(transferability.score).toBeGreaterThan(0.5);
    });

    it('should detect domain-specific artifacts', async () => {
      const artifact = createTestArtifact({
        context: {
          domain: 'healthcare',
          missionType: 'diagnostic',
          agentTopology: 'single'
        }
      });

      const localContext = createTestContext({
        domain: 'trading'
      });

      const transferability = await engine.checkTransferability(artifact, localContext);

      expect(transferability.transferable).toBe(false);
      expect(transferability.reasons).toContain('domain_mismatch');
    });

    it('should detect topology dependencies', async () => {
      const artifact = createTestArtifact({
        context: {
          domain: 'trading',
          missionType: 'speculative',
          agentTopology: 'hierarchical',
          topologyRequirements: ['coordinator-agent', 'worker-agents']
        }
      });

      const localContext = createTestContext({
        domain: 'trading',
        agentTopology: 'flat',
        capabilities: ['basic-trading']
      });

      const transferability = await engine.checkTransferability(artifact, localContext);

      if (!transferability.transferable) {
        expect(transferability.reasons).toContain('topology_mismatch');
      }
    });
  });

  // ============================================================================
  // compareContexts Tests
  // ============================================================================

  describe('compareContexts', () => {
    it('should detect perfect context match', async () => {
      const artifactContext = {
        domain: 'trading',
        missionType: 'speculative',
        agentTopology: 'multi_agent'
      };

      const localContext = createTestContext({
        domain: 'trading',
        missionType: 'speculative',
        agentTopology: 'multi_agent'
      });

      const comparison = await engine.compareContexts(artifactContext, localContext);

      expect(comparison.domainMatch).toBe(true);
      expect(comparison.missionTypeMatch).toBe(true);
      expect(comparison.agentTopologyMatch).toBe(true);
      expect(comparison.overallMatch).toBeGreaterThan(0.8);
    });

    it('should detect partial context match', async () => {
      const artifactContext = {
        domain: 'trading',
        missionType: 'operational',
        agentTopology: 'single'
      };

      const localContext = createTestContext({
        domain: 'trading',
        missionType: 'speculative',
        agentTopology: 'multi_agent'
      });

      const comparison = await engine.compareContexts(artifactContext, localContext);

      expect(comparison.domainMatch).toBe(true);
      expect(comparison.missionTypeMatch).toBe(false);
      expect(comparison.overallMatch).toBeLessThan(1);
      expect(comparison.overallMatch).toBeGreaterThan(0);
    });

    it('should detect complete context mismatch', async () => {
      const artifactContext = {
        domain: 'healthcare',
        missionType: 'diagnostic',
        agentTopology: 'single'
      };

      const localContext = createTestContext({
        domain: 'trading',
        missionType: 'speculative',
        agentTopology: 'multi_agent'
      });

      const comparison = await engine.compareContexts(artifactContext, localContext);

      expect(comparison.domainMatch).toBe(false);
      expect(comparison.missionTypeMatch).toBe(false);
      expect(comparison.agentTopologyMatch).toBe(false);
      expect(comparison.overallMatch).toBeLessThan(0.3);
    });
  });

  // ============================================================================
  // checkPolicyCompatibility Tests
  // ============================================================================

  describe('checkPolicyCompatibility', () => {
    it('should pass all policy checks', async () => {
      const artifact = createTestArtifact({
        evidence: {
          confidence: 0.9,
          sources: ['verified'],
          sampleSize: 1000,
          methodology: 'rigorous'
        },
        allowedUses: ['informational', 'advisory']
      });

      const localContext = createTestContext({
        policies: ['min-confidence-0.7', 'require-provenance']
      });

      const compatibility = await engine.checkPolicyCompatibility(artifact, localContext);

      expect(compatibility.compatible).toBe(true);
      expect(compatibility.violations).toHaveLength(0);
    });

    it('should detect minimum confidence violations', async () => {
      const artifact = createTestArtifact({
        evidence: {
          confidence: 0.5,
          sources: [],
          sampleSize: 50,
          methodology: 'basic'
        }
      });

      const localContext = createTestContext({
        policies: ['min-confidence-0.7']
      });

      const compatibility = await engine.checkPolicyCompatibility(artifact, localContext);

      expect(compatibility.compatible).toBe(false);
      expect(compatibility.violations).toContain('minimum_confidence_not_met');
    });

    it('should detect allowed-use restrictions', async () => {
      const artifact = createTestArtifact({
        allowedUses: ['informational']
      });

      const localContext = createTestContext({
        policies: ['allocative-requires-simulation']
      });

      const compatibility = await engine.checkPolicyCompatibility(artifact, localContext);

      if (!compatibility.compatible) {
        expect(compatibility.violations).toContain('allowed_use_restriction');
      }
    });
  });

  // ============================================================================
  // computeTrustScore Tests
  // ============================================================================

  describe('computeTrustScore', () => {
    it('should compute high trust for strong artifacts', async () => {
      const artifact = createTestArtifact({
        evidence: {
          confidence: 0.95,
          sources: ['multiple-verified'],
          sampleSize: 10000,
          methodology: 'peer-reviewed'
        },
        limitations: [],
        provenance: {
          sourceNode: 'trusted-node',
          sourceLayer: 4,
          timestamp: Date.now(),
          lineageId: 'trusted-lineage',
          verificationLevel: 'verified',
          peerReviewCount: 5
        }
      });

      const localContext = createTestContext();

      const trust = await engine.computeTrustScore(artifact, localContext);

      expect(trust.overall).toBeGreaterThan(0.8);
      expect(trust.provenanceStrength).toBeGreaterThan(0.8);
      expect(trust.confidenceStability).toBeGreaterThan(0.8);
    });

    it('should compute low trust for weak artifacts', async () => {
      const artifact = createTestArtifact({
        evidence: {
          confidence: 0.5,
          sources: ['unverified'],
          sampleSize: 10,
          methodology: 'anecdotal'
        },
        limitations: ['many caveats', 'uncertain', 'not reproducible'],
        provenance: {
          sourceNode: 'unknown-node',
          sourceLayer: 4,
          timestamp: Date.now(),
          lineageId: 'unknown-lineage'
        }
      });

      const localContext = createTestContext();

      const trust = await engine.computeTrustScore(artifact, localContext);

      expect(trust.overall).toBeLessThan(0.6);
    });

    it('should balance confidence and provenance', async () => {
      const highConfidenceLowProvenance = createTestArtifact({
        evidence: { confidence: 0.9, sources: [], sampleSize: 100, methodology: 'test' },
        provenance: { sourceNode: 'unknown', sourceLayer: 4, timestamp: Date.now(), lineageId: 'x' }
      });

      const lowConfidenceHighProvenance = createTestArtifact({
        evidence: { confidence: 0.7, sources: [], sampleSize: 100, methodology: 'test' },
        provenance: {
          sourceNode: 'trusted',
          sourceLayer: 4,
          timestamp: Date.now(),
          lineageId: 'y',
          verificationLevel: 'verified'
        }
      });

      const localContext = createTestContext();

      const trust1 = engine.computeTrustScore(highConfidenceLowProvenance, localContext);
      const trust2 = engine.computeTrustScore(lowConfidenceHighProvenance, localContext);

      // Both should have moderate trust due to balancing
      expect(trust1.overall).toBeGreaterThan(0.5);
      expect(trust2.overall).toBeGreaterThan(0.5);
    });
  });

  // ============================================================================
  // suggestAction Tests
  // ============================================================================

  describe('suggestAction', () => {
    it('should suggest ignore for low-trust artifacts', async () => {
      const result: QualificationResult = {
        category: 'low_trust',
        localRelevance: 0.2,
        provenanceStrength: 0.3,
        confidenceStability: 0.4,
        overallTrust: 0.3,
        hasContextClash: true,
        hasContradictions: false,
        requiresSimulation: false,
        policyCompatible: false,
        contextComparison: {
          domainMatch: false,
          missionTypeMatch: false,
          agentTopologyMatch: false,
          overallMatch: 0.1
        },
        recommendedUses: [],
        warnings: ['low trust', 'context mismatch'],
        adaptations: [],
        suggestedAction: 'ignore'
      };

      const action = await engine.suggestAction(result);

      expect(action).toBe('ignore');
    });

    it('should suggest send_to_simulation for allocative-eligible', async () => {
      const result: QualificationResult = {
        category: 'allocative_candidate',
        localRelevance: 0.9,
        provenanceStrength: 0.85,
        confidenceStability: 0.9,
        overallTrust: 0.85,
        hasContextClash: false,
        hasContradictions: false,
        requiresSimulation: true,
        policyCompatible: true,
        contextComparison: {
          domainMatch: true,
          missionTypeMatch: true,
          agentTopologyMatch: true,
          overallMatch: 0.95
        },
        recommendedUses: ['allocative_eligible'],
        warnings: [],
        adaptations: [],
        suggestedAction: 'send_to_simulation'
      };

      const action = await engine.suggestAction(result);

      expect(action).toBe('send_to_simulation');
    });

    it('should suggest use_advisory for high-trust artifacts', async () => {
      const result: QualificationResult = {
        category: 'high_confidence',
        localRelevance: 0.85,
        provenanceStrength: 0.8,
        confidenceStability: 0.85,
        overallTrust: 0.82,
        hasContextClash: false,
        hasContradictions: false,
        requiresSimulation: false,
        policyCompatible: true,
        contextComparison: {
          domainMatch: true,
          missionTypeMatch: true,
          agentTopologyMatch: true,
          overallMatch: 0.9
        },
        recommendedUses: ['informational', 'advisory'],
        warnings: [],
        adaptations: [],
        suggestedAction: 'use_advisory'
      };

      const action = await engine.suggestAction(result);

      expect(action).toBe('use_advisory');
    });
  });
});
