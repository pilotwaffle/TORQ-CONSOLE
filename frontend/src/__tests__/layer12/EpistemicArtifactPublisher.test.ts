/**
 * Layer 12: Collective Intelligence Exchange
 * Unit Tests - EpistemicArtifactPublisher
 *
 * Tests the service that converts insights to federatable artifacts.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createEpistemicArtifactPublisher } from '@/services/layer12/EpistemicArtifactPublisher';
import type { PublishedInsight, Pattern, EpistemicArtifact, PublicationOptions } from '@/types/layer12/epistemic';

describe('EpistemicArtifactPublisher', () => {
  let publisher: ReturnType<typeof createEpistemicArtifactPublisher>;

  beforeEach(() => {
    publisher = createEpistemicArtifactPublisher();
    vi.clearAllMocks();
  });

  // ============================================================================
  // fromInsight Tests
  // ============================================================================

  describe('fromInsight', () => {
    it('should convert a PublishedInsight to an EpistemicArtifact', () => {
      const insight: PublishedInsight = {
        insightId: 'insight-001',
        claim: 'Trading volume predicts price movement',
        summary: 'High correlation between volume and subsequent price changes',
        domain: 'trading',
        missionType: 'speculative',
        agentTopology: 'multi_agent',
        confidence: 0.85,
        evidence: {
          sources: ['exchange-data', 'backtest'],
          sampleSize: 10000,
          methodology: 'statistical-analysis'
        },
        limitations: ['only tested on BTC', 'short time window'],
        sourceNode: 'node-1',
        sourceLayer: 4,
        createdAt: Date.now()
      };

      const artifact = publisher.fromInsight(insight, {
        originNode: 'node-1',
        originLayer: 4,
        version: '1.0.0'
      });

      expect(artifact).toBeDefined();
      expect(artifact.artifactId).toBe('insight-001');
      expect(artifact.claim).toBe(insight.claim);
      expect(artifact.summary).toBe(insight.summary);
      expect(artifact.context.domain).toBe(insight.domain);
      expect(artifact.evidence.confidence).toBe(0.85);
      expect(artifact.limitations).toEqual(insight.limitations);
    });

    it('should convert a Pattern to an EpistemicArtifact', () => {
      const pattern: Pattern = {
        patternId: 'pattern-001',
        name: 'Volume Surge Pattern',
        description: 'Volume spikes precede price increases',
        category: 'price_action',
        indicators: ['volume', 'price'],
        conditions: { volumeIncrease: '>50%', timeframe: '1h' },
        confidence: 0.9,
        domain: 'trading',
        evidence: {
          sources: ['historical-data'],
          sampleSize: 5000,
          methodology: 'pattern-recognition'
        },
        limitations: ['market-dependent'],
        sourceNode: 'node-2',
        createdAt: Date.now()
      };

      const artifact = publisher.fromInsight(pattern, {
        originNode: 'node-2',
        originLayer: 4,
        version: '1.0.0'
      });

      expect(artifact).toBeDefined();
      expect(artifact.artifactId).toBe('pattern-001');
      expect(artifact.artifactType).toBe('pattern');
      expect(artifact.claim).toContain('Volume Surge Pattern');
    });

    it('should include allowed uses based on confidence', () => {
      const insight: PublishedInsight = {
        insightId: 'insight-002',
        claim: 'Test claim',
        summary: 'Test summary',
        domain: 'testing',
        missionType: 'operational',
        agentTopology: 'single',
        confidence: 0.85,
        evidence: {
          sources: [],
          sampleSize: 100,
          methodology: 'test'
        },
        limitations: [],
        sourceNode: 'node-1',
        sourceLayer: 4,
        createdAt: Date.now()
      };

      const artifact = publisher.fromInsight(insight, {
        originNode: 'node-1',
        originLayer: 4,
        version: '1.0.0'
      });

      expect(artifact.allowedUses).toContain('informational');
      expect(artifact.allowedUses).toContain('advisory');
    });

    it('should set provenance correctly', () => {
      const insight: PublishedInsight = {
        insightId: 'insight-003',
        claim: 'Test claim',
        summary: 'Test summary',
        domain: 'testing',
        missionType: 'operational',
        agentTopology: 'single',
        confidence: 0.8,
        evidence: {
          sources: [],
          sampleSize: 50,
          methodology: 'test'
        },
        limitations: [],
        sourceNode: 'node-1',
        sourceLayer: 4,
        createdAt: 1700000000000
      };

      const artifact = publisher.fromInsight(insight, {
        originNode: 'node-1',
        originLayer: 4,
        version: '1.0.0'
      });

      expect(artifact.provenance.sourceNode).toBe('node-1');
      expect(artifact.provenance.sourceLayer).toBe(4);
      expect(artifact.provenance.timestamp).toBe(1700000000000);
      expect(artifact.provenance.lineageId).toBeDefined();
    });
  });

  // ============================================================================
  // redactForFederation Tests
  // ============================================================================

  describe('redactForFederation', () => {
    it('should redact local references from context', () => {
      const artifact: EpistemicArtifact = {
        artifactId: 'artifact-001',
        artifactType: 'observational',
        originNode: 'node-1',
        originLayer: 4,
        createdAt: Date.now(),
        version: '1.0.0',
        claim: 'Local pattern discovered',
        summary: 'Pattern specific to local data',
        context: {
          domain: 'trading',
          missionType: 'speculative',
          agentTopology: 'multi_agent',
          localReferences: ['local-db-001', 'internal-cache']
        },
        evidence: {
          confidence: 0.8,
          sources: ['local-datasource'],
          sampleSize: 100,
          methodology: 'test'
        },
        limitations: [],
        allowedUses: ['informational'],
        provenance: {
          sourceNode: 'node-1',
          sourceLayer: 4,
          timestamp: Date.now(),
          lineageId: 'lineage-001'
        }
      };

      const redacted = publisher.redactForFederation(artifact);

      expect(redacted.redactedFields).toContain('context.localReferences');
    });

    it('should mark sources as federated when appropriate', () => {
      const artifact: EpistemicArtifact = {
        artifactId: 'artifact-002',
        artifactType: 'pattern',
        originNode: 'node-1',
        originLayer: 4,
        createdAt: Date.now(),
        version: '1.0.0',
        claim: 'Global trading pattern',
        summary: 'Pattern observed across multiple exchanges',
        context: {
          domain: 'trading',
          missionType: 'operational',
          agentTopology: 'single'
        },
        evidence: {
          confidence: 0.85,
          sources: ['binance', 'coinbase', 'kraken'],
          sampleSize: 10000,
          methodology: 'statistical-analysis'
        },
        limitations: ['exchange-specific fees not considered'],
        allowedUses: ['advisory'],
        provenance: {
          sourceNode: 'node-1',
          sourceLayer: 4,
          timestamp: Date.now(),
          lineageId: 'lineage-002'
        }
      };

      const redacted = publisher.redactForFederation(artifact);

      expect(redacted.redactedFields).toHaveLength(0);
    });

    it('should preserve essential information', () => {
      const artifact: EpistemicArtifact = {
        artifactId: 'artifact-003',
        artifactType: 'causal',
        originNode: 'node-1',
        originLayer: 4,
        createdAt: Date.now(),
        version: '1.0.0',
        claim: 'X causes Y',
        summary: 'Causal relationship discovered',
        context: {
          domain: 'testing',
          missionType: 'experimental',
          agentTopology: 'single'
        },
        evidence: {
          confidence: 0.9,
          sources: [],
          sampleSize: 1000,
          methodology: 'controlled-experiment'
        },
        limitations: ['lab conditions only'],
        allowedUses: ['simulation_only'],
        provenance: {
          sourceNode: 'node-1',
          sourceLayer: 4,
          timestamp: Date.now(),
          lineageId: 'lineage-003'
        }
      };

      const redacted = publisher.redactForFederation(artifact);

      expect(redacted.artifact.claim).toBe('X causes Y');
      expect(redacted.artifact.summary).toBe('Causal relationship discovered');
      expect(redacted.artifact.evidence.confidence).toBe(0.9);
    });
  });

  // ============================================================================
  // validateForPublication Tests
  // ============================================================================

  describe('validateForPublication', () => {
    it('should pass validation for high-confidence artifact', () => {
      const artifact: EpistemicArtifact = {
        artifactId: 'artifact-004',
        artifactType: 'observational',
        originNode: 'node-1',
        originLayer: 4,
        createdAt: Date.now(),
        version: '1.0.0',
        claim: 'Valid claim',
        summary: 'Valid summary',
        context: {
          domain: 'testing',
          missionType: 'operational',
          agentTopology: 'single'
        },
        evidence: {
          confidence: 0.85,
          sources: ['reliable-source'],
          sampleSize: 100,
          methodology: 'sound-method'
        },
        limitations: [],
        allowedUses: ['informational'],
        provenance: {
          sourceNode: 'node-1',
          sourceLayer: 4,
          timestamp: Date.now(),
          lineageId: 'lineage-004'
        }
      };

      const result = publisher.validateForPublication(artifact);

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should fail validation for low-confidence artifact', () => {
      const artifact: EpistemicArtifact = {
        artifactId: 'artifact-005',
        artifactType: 'observational',
        originNode: 'node-1',
        originLayer: 4,
        createdAt: Date.now(),
        version: '1.0.0',
        claim: 'Uncertain claim',
        summary: 'Low confidence observation',
        context: {
          domain: 'testing',
          missionType: 'exploratory',
          agentTopology: 'single'
        },
        evidence: {
          confidence: 0.5,
          sources: [],
          sampleSize: 5,
          methodology: 'guess'
        },
        limitations: ['very uncertain'],
        allowedUses: ['informational'],
        provenance: {
          sourceNode: 'node-1',
          sourceLayer: 4,
          timestamp: Date.now(),
          lineageId: 'lineage-005'
        }
      };

      const result = publisher.validateForPublication(artifact);

      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('should fail validation without proper context', () => {
      const artifact: EpistemicArtifact = {
        artifactId: 'artifact-006',
        artifactType: 'observational',
        originNode: 'node-1',
        originLayer: 4,
        createdAt: Date.now(),
        version: '1.0.0',
        claim: 'Context-less claim',
        summary: 'No context provided',
        context: {
          domain: '',
          missionType: '',
          agentTopology: ''
        },
        evidence: {
          confidence: 0.9,
          sources: [],
          sampleSize: 100,
          methodology: 'test'
        },
        limitations: [],
        allowedUses: ['informational'],
        provenance: {
          sourceNode: 'node-1',
          sourceLayer: 4,
          timestamp: Date.now(),
          lineageId: 'lineage-006'
        }
      };

      const result = publisher.validateForPublication(artifact);

      expect(result.valid).toBe(false);
    });
  });

  // ============================================================================
  // publishArtifact Tests
  // ============================================================================

  describe('publishArtifact', () => {
    it('should publish a valid artifact successfully', async () => {
      const insight: PublishedInsight = {
        insightId: 'insight-004',
        claim: 'Publishable insight',
        summary: 'Ready for federation',
        domain: 'trading',
        missionType: 'operational',
        agentTopology: 'single',
        confidence: 0.9,
        evidence: {
          sources: ['verified-source'],
          sampleSize: 1000,
          methodology: 'rigorous-analysis'
        },
        limitations: ['minor caveat'],
        sourceNode: 'node-1',
        sourceLayer: 4,
        createdAt: Date.now()
      };

      const options: PublicationOptions = {
        originNode: 'node-1',
        originLayer: 4,
        version: '1.0.0'
      };

      const result = await publisher.publishArtifact(insight, options);

      expect(result.success).toBe(true);
      expect(result.artifact).toBeDefined();
      expect(result.artifact.artifactId).toBe('insight-004');
    });

    it('should fail to publish invalid artifact', async () => {
      const insight: PublishedInsight = {
        insightId: 'insight-005',
        claim: 'Weak insight',
        summary: 'Not ready for federation',
        domain: 'testing',
        missionType: 'exploratory',
        agentTopology: 'single',
        confidence: 0.4,
        evidence: {
          sources: [],
          sampleSize: 3,
          methodology: 'hunch'
        },
        limitations: ['very uncertain', 'small sample'],
        sourceNode: 'node-1',
        sourceLayer: 4,
        createdAt: Date.now()
      };

      const options: PublicationOptions = {
        originNode: 'node-1',
        originLayer: 4,
        version: '1.0.0'
      };

      const result = await publisher.publishArtifact(insight, options);

      expect(result.success).toBe(false);
      expect(result.errors).toBeDefined();
      expect(result.errors.length).toBeGreaterThan(0);
    });
  });
});
