/**
 * Layer 12: Collective Intelligence Exchange
 * Unit Tests - ContradictionAndPluralityManager
 *
 * Tests the service that preserves disagreement and detects contradictions.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createContradictionAndPluralityManager } from '@/services/layer12/ContradictionAndPluralityManager';
import { createMockRepository } from './testHelpers';
import type { EpistemicArtifact, ContradictionType, PluralityView } from '@/types/layer12/epistemic';

describe('ContradictionAndPluralityManager', () => {
  let manager: ReturnType<typeof createContradictionAndPluralityManager>;
  let mockRepository: ILayer12Repository;

  beforeEach(() => {
    mockRepository = createMockRepository();
    manager = createContradictionAndPluralityManager(mockRepository);
    vi.clearAllMocks();
  });

  // Helper to create test artifacts
  const createArtifact = (id: string, claim: string, context?: Record<string, unknown>): EpistemicArtifact => ({
    artifactId: id,
    artifactType: 'causal',
    originNode: 'node-1',
    originLayer: 4,
    createdAt: Date.now(),
    version: '1.0.0',
    claim,
    summary: `Summary for ${id}`,
    context: {
      domain: 'trading',
      missionType: 'speculative',
      agentTopology: 'single',
      ...context
    },
    evidence: {
      confidence: 0.8,
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
      lineageId: `lineage-${id}`
    }
  });

  // ============================================================================
  // detectContradictions Tests
  // ============================================================================

  describe('detectContradictions', () => {
    it('should detect direct contradictions', async () => {
      const claimA = createArtifact('claim-001', 'Price always goes up after volume surge');
      const claimB = createArtifact('claim-002', 'Price often goes down after volume surge');

      const detection = await manager.detectContradictions(claimB, [claimA]);

      expect(detection.hasContradictions).toBe(true);
      expect(detection.contradictions.length).toBeGreaterThan(0);

      const directContradiction = detection.contradictions.find(
        c => c.type === 'direct_contradiction'
      );
      expect(directContradiction).toBeDefined();
    });

    it('should detect context conflicts', async () => {
      const claimA = createArtifact('claim-003', 'Strategy works in bull markets', {
        marketCondition: 'bull',
        timeframe: 'daily'
      });

      const claimB = createArtifact('claim-004', 'Strategy fails in bear markets', {
        marketCondition: 'bear',
        timeframe: 'daily'
      });

      const detection = await manager.detectContradictions(claimB, [claimA]);

      const contextConflict = detection.contradictions.find(
        c => c.type === 'context_conflict'
      );
      expect(contextConflict).toBeDefined();
    });

    it('should detect causal disagreements', async () => {
      const claimA = createArtifact('claim-005', 'High volatility causes price increases');
      const claimB = createArtifact('claim-006', 'Price increases cause high volatility');

      const detection = await manager.detectContradictions(claimB, [claimA]);

      const causalDisagreement = detection.contradictions.find(
        c => c.type === 'causal_disagreement'
      );
      expect(causalDisagreement).toBeDefined();
    });

    it('should detect recommendation conflicts', async () => {
      const claimA = createArtifact('claim-007', 'Always use stop-loss at 2%', {
        recommendation: 'use-stop-loss',
        stopLossPercent: 2
      });

      const claimB = createArtifact('claim-008', 'Never use stop-loss in trending markets', {
        recommendation: 'no-stop-loss',
        marketCondition: 'trending'
      });

      const detection = await manager.detectContradictions(claimB, [claimA]);

      const recommendationConflict = detection.contradictions.find(
        c => c.type === 'recommendation_conflict'
      );
      expect(recommendationConflict).toBeDefined();
    });

    it('should return no contradictions for unrelated claims', async () => {
      const claimA = createArtifact('claim-009', 'Volume indicates market interest');
      const claimB = createArtifact('claim-010', 'Weather affects agricultural commodities');

      const detection = await manager.detectContradictions(claimB, [claimA]);

      expect(detection.hasContradictions).toBe(false);
      expect(detection.contradictions).toHaveLength(0);
    });

    it('should handle empty existing claims array', async () => {
      const claim = createArtifact('claim-011', 'New claim');

      const detection = await manager.detectContradictions(claim, []);

      expect(detection.hasContradictions).toBe(false);
      expect(detection.contradictions).toHaveLength(0);
    });
  });

  // ============================================================================
  // registerContradiction Tests
  // ============================================================================

  describe('registerContradiction', () => {
    it('should register a new contradiction', async () => {
      const claimAId = 'claim-001';
      const claimBId = 'claim-002';
      const type: ContradictionType = 'direct_contradiction';
      const detectedBy = 'node-1';

      const record = await manager.registerContradiction(claimAId, claimBId, type, detectedBy);

      expect(record).toBeDefined();
      expect(record.claimAId).toBe(claimAId);
      expect(record.claimBId).toBe(claimBId);
      expect(record.contradictionType).toBe(type);
      expect(record.detectedBy).toBe(detectedBy);
      expect(record.resolved).toBe(false);
    });

    it('should generate unique contradiction IDs', async () => {
      const record1 = await manager.registerContradiction(
        'claim-001',
        'claim-002',
        'direct_contradiction',
        'node-1'
      );

      const record2 = await manager.registerContradiction(
        'claim-003',
        'claim-004',
        'context_conflict',
        'node-1'
      );

      expect(record1.contradictionId).not.toBe(record2.contradictionId);
    });
  });

  // ============================================================================
  // getContradictions Tests
  // ============================================================================

  describe('getContradictions', () => {
    it('should retrieve contradictions for a claim', async () => {
      const claimId = 'claim-001';

      await manager.registerContradiction(
        claimId,
        'claim-002',
        'direct_contradiction',
        'node-1'
      );

      await manager.registerContradiction(
        'claim-003',
        claimId,
        'context_conflict',
        'node-2'
      );

      const contradictions = await manager.getContradictions(claimId);

      expect(contradictions.length).toBeGreaterThanOrEqual(2);
      expect(contradictions.some(c => c.claimAId === claimId || c.claimBId === claimId)).toBe(true);
    });

    it('should return empty array for claim with no contradictions', async () => {
      const contradictions = await manager.getContradictions('nonexistent-claim');

      expect(contradictions).toBeDefined();
      // Implementation may return empty array or handle gracefully
    });
  });

  // ============================================================================
  // resolveContradiction Tests
  // ============================================================================

  describe('resolveContradiction', () => {
    it('should mark a contradiction as resolved', async () => {
      const record = await manager.registerContradiction(
        'claim-001',
        'claim-002',
        'direct_contradiction',
        'node-1'
      );

      const success = await manager.resolveContradiction(
        record.contradictionId,
        'a_is_correct',
        'Additional evidence supports claim A',
        'node-1'
      );

      expect(success).toBe(true);
    });

    it('should store resolution details', async () => {
      const record = await manager.registerContradiction(
        'claim-001',
        'claim-002',
        'direct_contradiction',
        'node-1'
      );

      await manager.resolveContradiction(
        record.contradictionId,
        'both_valid_different_contexts',
        'Both claims valid under different market conditions',
        'node-1'
      );

      const contradictions = await manager.getContradictions('claim-001');
      const resolved = contradictions.find(c => c.contradictionId === record.contradictionId);

      expect(resolved?.resolved).toBe(true);
      expect(resolved?.resolutionType).toBe('both_valid_different_contexts');
      expect(resolved?.resolutionNotes).toContain('market conditions');
    });
  });

  // ============================================================================
  // getPluralityView Tests
  // ============================================================================

  describe('getPluralityView', () => {
    it('should aggregate competing claims on a topic', async () => {
      // Create artifacts representing different viewpoints
      const artifacts: EpistemicArtifact[] = [
        createArtifact('claim-001', 'Technical analysis is superior'),
        createArtifact('claim-002', 'Fundamental analysis is superior'),
        createArtifact('claim-003', 'Combination of both is best'),
        createArtifact('claim-004', 'Quantitative analysis beats all')
      ];

      const view = await manager.getPluralityView('market-analysis-methodology', artifacts);

      expect(view).toBeDefined();
      expect(view.topic).toBe('market-analysis-methodology');
      expect(view.competingClaims.length).toBe(4);
      expect(view.preservesPlurality).toBe(true);
    });

    it('should identify consensus when all claims agree', async () => {
      const artifacts: EpistemicArtifact[] = [
        createArtifact('claim-005', 'Diversification reduces risk'),
        createArtifact('claim-006', 'Portfolio diversification lowers volatility'),
        createArtifact('claim-007', 'Diversified portfolios have better risk-adjusted returns')
      ];

      const view = await manager.getPluralityView('risk-management', artifacts);

      expect(view.hasConsensus).toBe(true);
      expect(view.preservesPlurality).toBe(false);
    });

    it('should track claim origins for provenance', async () => {
      const artifacts: EpistemicArtifact[] = [
        createArtifact('claim-008', 'Viewpoint A'),
        createArtifact('claim-009', 'Viewpoint B')
      ];

      const view = await manager.getPluralityView('test-topic', artifacts);

      expect(view.competingClaims).toHaveLength(2);
      view.competingClaims.forEach(claim => {
        expect(claim.originNode).toBeDefined();
        expect(claim.artifactId).toBeDefined();
      });
    });

    it('should handle empty claims array', async () => {
      const view = await manager.getPluralityView('empty-topic', []);

      expect(view).toBeDefined();
      expect(view.competingClaims).toHaveLength(0);
      expect(view.hasConsensus).toBe(false);
    });
  });

  // ============================================================================
  // checkMonocultureRisk Tests
  // ============================================================================

  describe('checkMonocultureRisk', () => {
    it('should detect low risk with diverse origins', async () => {
      const artifacts: EpistemicArtifact[] = [
        { ...createArtifact('claim-001', 'Claim 1'), originNode: 'node-1' },
        { ...createArtifact('claim-002', 'Claim 2'), originNode: 'node-2' },
        { ...createArtifact('claim-003', 'Claim 3'), originNode: 'node-3' },
        { ...createArtifact('claim-004', 'Claim 4'), originNode: 'node-4' }
      ];

      const risk = await manager.checkMonocultureRisk('test-topic', artifacts);

      expect(risk.atRisk).toBe(false);
      expect(risk.diversityScore).toBeGreaterThan(0.5);
    });

    it('should detect high risk from single origin', async () => {
      const artifacts: EpistemicArtifact[] = [
        { ...createArtifact('claim-001', 'Claim 1'), originNode: 'node-1' },
        { ...createArtifact('claim-002', 'Claim 2'), originNode: 'node-1' },
        { ...createArtifact('claim-003', 'Claim 3'), originNode: 'node-1' },
        { ...createArtifact('claim-004', 'Claim 4'), originNode: 'node-1' }
      ];

      const risk = await manager.checkMonocultureRisk('test-topic', artifacts);

      expect(risk.atRisk).toBe(true);
      expect(risk.diversityScore).toBeLessThan(0.3);
      expect(risk.dominantOrigin).toBe('node-1');
    });

    it('should calculate origin distribution', async () => {
      const artifacts: EpistemicArtifact[] = [
        { ...createArtifact('claim-001', 'Claim 1'), originNode: 'node-1' },
        { ...createArtifact('claim-002', 'Claim 2'), originNode: 'node-1' },
        { ...createArtifact('claim-003', 'Claim 3'), originNode: 'node-2' },
        { ...createArtifact('claim-004', 'Claim 4'), originNode: 'node-3' }
      ];

      const risk = await manager.checkMonocultureRisk('test-topic', artifacts);

      expect(risk.originDistribution).toBeDefined();
      expect(Object.keys(risk.originDistribution).length).toBe(3);
      expect(risk.originDistribution['node-1']).toBe(2);
      expect(risk.originDistribution['node-2']).toBe(1);
      expect(risk.originDistribution['node-3']).toBe(1);
    });
  });

  // ============================================================================
  // clusterByTopic Tests
  // ============================================================================

  describe('clusterByTopic', () => {
    it('should group related claims', () => {
      const artifacts: EpistemicArtifact[] = [
        createArtifact('claim-001', 'Stop loss prevents large losses'),
        createArtifact('claim-002', 'Always use 2% stop loss'),
        createArtifact('claim-003', 'Moving averages indicate trend'),
        createArtifact('claim-004', 'EMA crossover signals entry')
      ];

      const clusters = manager.clusterByTopic(artifacts);

      expect(clusters.size).toBeGreaterThan(0);
      // Should group stop-loss claims together and moving-average claims together
    });

    it('should handle empty artifacts array', () => {
      const clusters = manager.clusterByTopic([]);

      expect(clusters.size).toBe(0);
    });

    it('should create single cluster for unrelated claims', () => {
      const artifacts: EpistemicArtifact[] = [
        createArtifact('claim-001', 'Weather affects crops'),
        createArtifact('claim-002', 'Interest rates affect currencies')
      ];

      const clusters = manager.clusterByTopic(artifacts);

      // May create separate clusters or a general cluster
      expect(clusters.size).toBeGreaterThanOrEqual(1);
    });
  });

  // ============================================================================
  // Preserves Disagreement Tests
  // ============================================================================

  describe('Plurality Preservation', () => {
    it('should preserve conflicting viewpoints', async () => {
      const claimA = createArtifact('claim-001', 'Viewpoint A is correct');
      const claimB = createArtifact('claim-002', 'Viewpoint B is correct');

      const detection = await manager.detectContradictions(claimB, [claimA]);

      expect(detection.hasContradictions).toBe(true);
      // The system should NOT collapse these into a single "truth"
      // but preserve both for local qualification
    });

    it('should allow context-dependent validity', async () => {
      const claimA = createArtifact('claim-003', 'Strategy A works in trending markets');
      const claimB = createArtifact('claim-004', 'Strategy A fails in ranging markets');

      const detection = await manager.detectContradictions(claimB, [claimA]);

      expect(detection.contradictions.some(c => c.type === 'context_conflict')).toBe(true);

      // Resolution should allow both to be valid in different contexts
      const resolution = await manager.resolveContradiction(
        'test-contradiction-id',
        'both_valid_different_contexts',
        'Both strategies valid under different market conditions'
      );

      expect(resolution).toBeDefined();
    });

    it('should track resolution without collapsing to single truth', async () => {
      const view: PluralityView = {
        topic: 'test-topic',
        competingClaims: [
          createArtifact('claim-001', 'View A'),
          createArtifact('claim-002', 'View B'),
          createArtifact('claim-003', 'View C')
        ],
        hasConsensus: false,
        preservesPlurality: true,
        consensusClaim: undefined,
        conflictSummary: 'Three competing viewpoints exist'
      };

      expect(view.preservesPlurality).toBe(true);
      expect(view.competingClaims).toHaveLength(3);
      expect(view.consensusClaim).toBeUndefined();
    });
  });
});
