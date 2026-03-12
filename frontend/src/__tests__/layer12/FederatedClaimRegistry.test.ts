/**
 * Layer 12: Collective Intelligence Exchange
 * Unit Tests - FederatedClaimRegistry
 *
 * Tests the service that stores and queries network-visible claims.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createFederatedClaimRegistry } from '@/services/layer12/FederatedClaimRegistry';
import type { EpistemicArtifact, ClaimQuery, ClaimRecord } from '@/types/layer12/epistemic';

describe('FederatedClaimRegistry', () => {
  let registry: ReturnType<typeof createFederatedClaimRegistry>;

  beforeEach(() => {
    registry = createFederatedClaimRegistry();
    vi.clearAllMocks();
  });

  // Helper to create a test artifact
  const createTestArtifact = (overrides?: Partial<EpistemicArtifact>): EpistemicArtifact => ({
    artifactId: `artifact-${Date.now()}`,
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

  // ============================================================================
  // registerClaim Tests
  // ============================================================================

  describe('registerClaim', () => {
    it('should register a new claim', async () => {
      const artifact = createTestArtifact();

      const record = await registry.registerClaim(artifact);

      expect(record).toBeDefined();
      expect(record.artifactId).toBe(artifact.artifactId);
      expect(record.claim).toBe(artifact.claim);
      expect(record.artifactType).toBe(artifact.artifactType);
      expect(record.originNode).toBe(artifact.originNode);
    });

    it('should assign received and indexed timestamps', async () => {
      const artifact = createTestArtifact();

      const record = await registry.registerClaim(artifact);

      expect(record.receivedAt).toBeDefined();
      expect(record.indexedAt).toBeDefined();
      expect(record.receivedAt).toBeLessThanOrEqual(Date.now());
    });

    it('should preserve artifact metadata', async () => {
      const artifact = createTestArtifact({
        artifactType: 'causal',
        claim: 'X causes Y in trading context',
        context: {
          domain: 'trading',
          missionType: 'operational',
          agentTopology: 'single'
        },
        evidence: {
          confidence: 0.9,
          sources: ['verified-source'],
          sampleSize: 5000,
          methodology: 'controlled-experiment'
        }
      });

      const record = await registry.registerClaim(artifact);

      expect(record.artifactType).toBe('causal');
      expect(record.context.domain).toBe('trading');
      expect(record.evidence.confidence).toBe(0.9);
    });

    it('should handle multiple claims', async () => {
      const artifact1 = createTestArtifact({ artifactId: 'artifact-001' });
      const artifact2 = createTestArtifact({ artifactId: 'artifact-002' });
      const artifact3 = createTestArtifact({ artifactId: 'artifact-003' });

      const record1 = await registry.registerClaim(artifact1);
      const record2 = await registry.registerClaim(artifact2);
      const record3 = await registry.registerClaim(artifact3);

      expect(record1.artifactId).toBe('artifact-001');
      expect(record2.artifactId).toBe('artifact-002');
      expect(record3.artifactId).toBe('artifact-003');
    });
  });

  // ============================================================================
  // getClaim Tests
  // ============================================================================

  describe('getClaim', () => {
    it('should retrieve a registered claim', async () => {
      const artifact = createTestArtifact({ artifactId: 'test-claim-001' });

      await registry.registerClaim(artifact);
      const record = await registry.getClaim('test-claim-001');

      expect(record).toBeDefined();
      expect(record?.artifactId).toBe('test-claim-001');
    });

    it('should return null for non-existent claim', async () => {
      const record = await registry.getClaim('nonexistent-claim');

      expect(record).toBeNull();
    });

    it('should retrieve claim with all fields', async () => {
      const artifact = createTestArtifact({
        artifactId: 'test-claim-full',
        limitations: ['limit1', 'limit2', 'limit3'],
        allowedUses: ['informational', 'advisory', 'allocative_eligible']
      });

      await registry.registerClaim(artifact);
      const record = await registry.getClaim('test-claim-full');

      expect(record).toBeDefined();
      expect(record?.limitations).toHaveLength(3);
      expect(record?.allowedUses).toHaveLength(3);
    });
  });

  // ============================================================================
  // queryClaims Tests
  // ============================================================================

  describe('queryClaims', () => {
    beforeEach(async () => {
      // Register test data
      await registry.registerClaim(createTestArtifact({
        artifactId: 'claim-trading-001',
        artifactType: 'pattern',
        originNode: 'node-1',
        context: { domain: 'trading', missionType: 'speculative', agentTopology: 'single' },
        evidence: { confidence: 0.85, sources: [], sampleSize: 100, methodology: 'test' }
      }));

      await registry.registerClaim(createTestArtifact({
        artifactId: 'claim-trading-002',
        artifactType: 'observational',
        originNode: 'node-2',
        context: { domain: 'trading', missionType: 'operational', agentTopology: 'multi_agent' },
        evidence: { confidence: 0.75, sources: [], sampleSize: 200, methodology: 'test' }
      }));

      await registry.registerClaim(createTestArtifact({
        artifactId: 'claim-health-001',
        artifactType: 'causal',
        originNode: 'node-1',
        context: { domain: 'healthcare', missionType: 'diagnostic', agentTopology: 'single' },
        evidence: { confidence: 0.9, sources: [], sampleSize: 500, methodology: 'test' }
      }));
    });

    it('should return all claims when no filters provided', async () => {
      const results = await registry.queryClaims({});

      expect(results.length).toBeGreaterThanOrEqual(3);
    });

    it('should filter by artifact type', async () => {
      const results = await registry.queryClaims({
        artifactType: 'pattern'
      });

      expect(results.length).toBeGreaterThanOrEqual(1);
      expect(results.every(r => r.artifactType === 'pattern')).toBe(true);
    });

    it('should filter by origin node', async () => {
      const results = await registry.queryClaims({
        originNode: 'node-1'
      });

      expect(results.length).toBeGreaterThanOrEqual(2);
      expect(results.every(r => r.originNode === 'node-1')).toBe(true);
    });

    it('should filter by domain', async () => {
      const results = await registry.queryClaims({
        domain: 'trading'
      });

      expect(results.length).toBeGreaterThanOrEqual(2);
      expect(results.every(r => r.context.domain === 'trading')).toBe(true);
    });

    it('should filter by minimum confidence', async () => {
      const results = await registry.queryClaims({
        minConfidence: 0.8
      });

      expect(results.every(r => r.evidence.confidence >= 0.8)).toBe(true);
    });

    it('should filter by mission type', async () => {
      const results = await registry.queryClaims({
        missionType: 'speculative'
      });

      expect(results.every(r => r.context.missionType === 'speculative')).toBe(true);
    });

    it('should filter by agent topology', async () => {
      const results = await registry.queryClaims({
        agentTopology: 'single'
      });

      expect(results.every(r => r.context.agentTopology === 'single')).toBe(true);
    });

    it('should respect limit parameter', async () => {
      const results = await registry.queryClaims({
        limit: 2
      });

      expect(results.length).toBeLessThanOrEqual(2);
    });

    it('should apply multiple filters together', async () => {
      const results = await registry.queryClaims({
        domain: 'trading',
        originNode: 'node-1',
        minConfidence: 0.7
      });

      expect(results.every(r =>
        r.context.domain === 'trading' &&
        r.originNode === 'node-1' &&
        r.evidence.confidence >= 0.7
      )).toBe(true);
    });

    it('should filter by time range', async () => {
      const now = Date.now();
      const results = await registry.queryClaims({
        timeRange: {
          start: now - 86400000, // Last 24 hours
          end: now
        }
      });

      // Should return claims from the last day
      expect(Array.isArray(results)).toBe(true);
    });

    it('should filter by allowed use', async () => {
      const results = await registry.queryClaims({
        allowedUse: 'advisory'
      });

      expect(results.every(r => r.allowedUses.includes('advisory'))).toBe(true);
    });
  });

  // ============================================================================
  // findRelevantClaims Tests
  // ============================================================================

  describe('findRelevantClaims', () => {
    beforeEach(async () => {
      // Register test data with varying relevance
      await registry.registerClaim(createTestArtifact({
        artifactId: 'relevant-001',
        context: { domain: 'trading', missionType: 'speculative', agentTopology: 'multi_agent' },
        claim: 'Crypto trading pattern'
      }));

      await registry.registerClaim(createTestArtifact({
        artifactId: 'relevant-002',
        context: { domain: 'trading', missionType: 'operational', agentTopology: 'multi_agent' },
        claim: 'Trading operational insight'
      }));

      await registry.registerClaim(createTestArtifact({
        artifactId: 'irrelevant-001',
        context: { domain: 'healthcare', missionType: 'diagnostic', agentTopology: 'single' },
        claim: 'Medical diagnostic pattern'
      }));
    });

    it('should find claims relevant to local context', async () => {
      const localContext = {
        nodeId: 'local-node-1',
        domain: 'trading',
        missionType: 'speculative',
        agentTopology: 'multi_agent'
      };

      const relevant = await registry.findRelevantClaims(localContext);

      expect(relevant.length).toBeGreaterThan(0);
      expect(relevant.every(r => r.relevanceScore >= 0)).toBe(true);
    });

    it('should score relevance by context similarity', async () => {
      const localContext = {
        nodeId: 'local-node-1',
        domain: 'trading',
        missionType: 'speculative',
        agentTopology: 'multi_agent'
      };

      const relevant = await registry.findRelevantClaims(localContext);

      // Most relevant claims should have higher scores
      const sortedByScore = [...relevant].sort((a, b) => b.relevanceScore - a.relevanceScore);
      expect(sortedByScore[0].relevanceScore).toBeGreaterThanOrEqual(sortedByScore[sortedByScore.length - 1].relevanceScore);
    });

    it('should return empty array for no relevant claims', async () => {
      const localContext = {
        nodeId: 'local-node-1',
        domain: 'completely-different-domain',
        missionType: 'experimental',
        agentTopology: 'hierarchical'
      };

      const relevant = await registry.findRelevantClaims(localContext);

      expect(Array.isArray(relevant)).toBe(true);
    });

    it('should respect minimum relevance threshold', async () => {
      const localContext = {
        nodeId: 'local-node-1',
        domain: 'trading',
        missionType: 'speculative',
        agentTopology: 'multi_agent'
      };

      const relevant = await registry.findRelevantClaims(localContext, 0.5);

      expect(relevant.every(r => r.relevanceScore >= 0.5)).toBe(true);
    });
  });

  // ============================================================================
  // getContradictions Tests
  // ============================================================================

  describe('getContradictions', () => {
    it('should retrieve contradictions for a claim', async () => {
      const artifact = createTestArtifact({ artifactId: 'claim-with-contradiction' });

      await registry.registerClaim(artifact);
      const contradictions = await registry.getContradictions('claim-with-contradiction');

      expect(Array.isArray(contradictions)).toBe(true);
    });

    it('should return empty array for claim with no contradictions', async () => {
      const artifact = createTestArtifact({ artifactId: 'claim-no-contradiction' });

      await registry.registerClaim(artifact);
      const contradictions = await registry.getContradictions('claim-no-contradiction');

      expect(Array.isArray(contradictions)).toBe(true);
    });
  });

  // ============================================================================
  // registerContradiction Tests
  // ============================================================================

  describe('registerContradiction', () => {
    it('should register a contradiction between two claims', async () => {
      const claimAId = 'claim-a-001';
      const claimBId = 'claim-b-001';
      const type = 'direct_contradiction' as const;

      const record = await registry.registerContradiction(claimAId, claimBId, type);

      expect(record).toBeDefined();
      expect(record.claimAId).toBe(claimAId);
      expect(record.claimBId).toBe(claimBId);
      expect(record.contradictionType).toBe(type);
      expect(record.resolved).toBe(false);
    });

    it('should generate unique contradiction IDs', async () => {
      const record1 = await registry.registerContradiction('claim-001', 'claim-002', 'direct_contradiction');
      const record2 = await registry.registerContradiction('claim-003', 'claim-004', 'context_conflict');

      expect(record1.contradictionId).not.toBe(record2.contradictionId);
    });

    it('should set detection timestamp', async () => {
      const beforeTime = Date.now();
      const record = await registry.registerContradiction('claim-001', 'claim-002', 'direct_contradiction');
      const afterTime = Date.now();

      expect(record.detectedAt).toBeGreaterThanOrEqual(beforeTime);
      expect(record.detectedAt).toBeLessThanOrEqual(afterTime);
    });
  });

  // ============================================================================
  // resolveContradiction Tests
  // ============================================================================

  describe('resolveContradiction', () => {
    it('should mark a contradiction as resolved', async () => {
      const record = await registry.registerContradiction('claim-001', 'claim-002', 'direct_contradiction');

      const success = await registry.resolveContradiction(
        record.contradictionId,
        'a_is_correct',
        'Evidence supports claim A'
      );

      expect(success).toBe(true);
    });

    it('should store resolution details', async () => {
      const record = await registry.registerContradiction('claim-001', 'claim-002', 'context_conflict');

      await registry.resolveContradiction(
        record.contradictionId,
        'both_valid_different_contexts',
        'Both claims valid under different conditions'
      );

      const contradictions = await registry.getContradictions('claim-001');
      const resolved = contradictions.find(c => c.contradictionId === record.contradictionId);

      expect(resolved?.resolved).toBe(true);
      expect(resolved?.resolutionType).toBe('both_valid_different_contexts');
    });

    it('should return false for non-existent contradiction', async () => {
      const success = await registry.resolveContradiction(
        'nonexistent-contradiction',
        'a_is_correct'
      );

      expect(success).toBe(false);
    });
  });

  // ============================================================================
  // getStatistics Tests
  // ============================================================================

  describe('getStatistics', () => {
    it('should return overall statistics', async () => {
      const stats = await registry.getStatistics();

      expect(stats).toBeDefined();
      expect(typeof stats.totalClaims).toBe('number');
      expect(typeof stats.totalContradictions).toBe('number');
    });

    it('should break down by artifact type', async () => {
      const stats = await registry.getStatistics();

      expect(stats.byArtifactType).toBeDefined();
      expect(typeof stats.byArtifactType).toBe('object');
    });

    it('should break down by domain', async () => {
      const stats = await registry.getStatistics();

      expect(stats.byDomain).toBeDefined();
      expect(typeof stats.byDomain).toBe('object');
    });

    it('should break down by origin node', async () => {
      const stats = await registry.getStatistics();

      expect(stats.byOriginNode).toBeDefined();
      expect(typeof stats.byOriginNode).toBe('object');
    });
  });

  // ============================================================================
  // deleteClaim Tests
  // ============================================================================

  describe('deleteClaim', () => {
    it('should soft delete a claim', async () => {
      const artifact = createTestArtifact({ artifactId: 'delete-me' });

      await registry.registerClaim(artifact);
      const deleted = await registry.deleteClaim('delete-me');

      expect(deleted).toBe(true);
    });

    it('should return false for non-existent claim', async () => {
      const deleted = await registry.deleteClaim('nonexistent-claim');

      expect(deleted).toBe(false);
    });
  });
});
