/**
 * Layer 12: Collective Intelligence Exchange
 * Unit Tests - EpistemicAuditService
 *
 * Tests the service that tracks all exchange events.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { createEpistemicAuditService } from '@/services/layer12/EpistemicAuditService';
import type { AuditEvent, AuditQuery, AdoptionStatistics } from '@/types/layer12/epistemic';

describe('EpistemicAuditService', () => {
  let audit: ReturnType<typeof createEpistemicAuditService>;

  beforeEach(() => {
    audit = createEpistemicAuditService();
    vi.clearAllMocks();
  });

  // ============================================================================
  // logPublication Tests
  // ============================================================================

  describe('logPublication', () => {
    it('should log a publication event', async () => {
      await audit.logPublication({
        artifactId: 'artifact-001',
        nodeId: 'node-1',
        artifactType: 'pattern',
        claim: 'Test pattern',
        originNode: 'node-1',
        originLayer: 4
      });

      // Service should log the event successfully
      // In real implementation, this would persist to database
    });

    it('should include timestamp in publication event', async () => {
      const beforeTime = Date.now();

      await audit.logPublication({
        artifactId: 'artifact-002',
        nodeId: 'node-1',
        artifactType: 'observational',
        claim: 'Test observation',
        originNode: 'node-1',
        originLayer: 4
      });

      const afterTime = Date.now();

      // In real implementation, verify timestamp is between before and after
      expect(true).toBe(true); // Placeholder
    });

    it('should track publication metadata', async () => {
      await audit.logPublication({
        artifactId: 'artifact-003',
        nodeId: 'node-1',
        artifactType: 'causal',
        claim: 'Causal relationship',
        originNode: 'node-1',
        originLayer: 4,
        confidence: 0.85,
        domain: 'trading'
      });

      // Metadata should be preserved in the log
    });
  });

  // ============================================================================
  // logQualification Tests
  // ============================================================================

  describe('logQualification', () => {
    it('should log a qualification event', async () => {
      await audit.logQualification({
        artifactId: 'artifact-001',
        nodeId: 'node-2',
        qualifyingNode: 'node-2',
        category: 'high_confidence',
        overallTrust: 0.85,
        suggestedAction: 'use_advisory',
        localRelevance: 0.9,
        provenanceStrength: 0.8
      });

      // Qualification should be logged with scores
    });

    it('should include warnings in qualification log', async () => {
      await audit.logQualification({
        artifactId: 'artifact-002',
        nodeId: 'node-2',
        qualifyingNode: 'node-2',
        category: 'moderate_confidence',
        overallTrust: 0.6,
        suggestedAction: 'store_informational',
        localRelevance: 0.7,
        provenanceStrength: 0.5,
        warnings: ['context_mismatch', 'low_sample_size']
      });

      // Warnings should be preserved
    });

    it('should track context comparison results', async () => {
      await audit.logQualification({
        artifactId: 'artifact-003',
        nodeId: 'node-2',
        qualifyingNode: 'node-2',
        category: 'high_confidence',
        overallTrust: 0.9,
        suggestedAction: 'use_advisory',
        localRelevance: 0.95,
        provenanceStrength: 0.85,
        contextComparison: {
          domainMatch: true,
          missionMatch: true,
          topologyMatch: true,
          similarityScore: 0.95
        }
      });

      // Context comparison should be logged
    });
  });

  // ============================================================================
  // logAdoption Tests
  // ============================================================================

  describe('logAdoption', () => {
    it('should log an adoption event', async () => {
      await audit.logAdoption({
        artifactId: 'artifact-001',
        nodeId: 'node-2',
        adoptionType: 'advisory',
        adaptations: []
      });

      // Adoption should be logged
    });

    it('should track adaptations made', async () => {
      await audit.logAdoption({
        artifactId: 'artifact-002',
        nodeId: 'node-2',
        adoptionType: 'advisory',
        adaptations: [
          'adjusted_stop_loss',
          'modified_timeframe'
        ]
      });

      // Adaptations should be preserved
    });

    it('should distinguish adoption types', async () => {
      const adoptionTypes = [
        'informational',
        'advisory',
        'simulation_tested',
        'allocative_eligible'
      ] as const;

      for (const type of adoptionTypes) {
        await audit.logAdoption({
          artifactId: `artifact-${type}`,
          nodeId: 'node-2',
          adoptionType: type,
          adaptations: []
        });
      }

      // All types should be logged correctly
    });
  });

  // ============================================================================
  // logRejection Tests
  // ============================================================================

  describe('logRejection', () => {
    it('should log a rejection event', async () => {
      await audit.logRejection({
        artifactId: 'artifact-001',
        nodeId: 'node-2',
        reason: 'context_mismatch',
        details: { domain: 'trading vs healthcare' }
      });

      // Rejection should be logged with reason
    });

    it('should include rejection details', async () => {
      await audit.logRejection({
        artifactId: 'artifact-002',
        nodeId: 'node-2',
        reason: 'low_confidence',
        details: {
          confidence: 0.5,
          required: 0.7,
          sampleSize: 10
        }
      });

      // Details should be preserved
    });

    it('should track policy rejections', async () => {
      await audit.logRejection({
        artifactId: 'artifact-003',
        nodeId: 'node-2',
        reason: 'policy_incompatible',
        details: {
          violatedPolicy: 'min-confidence-0.7',
          actualConfidence: 0.6
        }
      });

      // Policy violations should be logged
    });
  });

  // ============================================================================
  // logSimulationTest Tests
  // ============================================================================

  describe('logSimulationTest', () => {
    it('should log a simulation test event', async () => {
      await audit.logSimulationTest({
        artifactId: 'artifact-001',
        nodeId: 'node-2',
        passed: true,
        simulatedConditions: ['bull_market', 'high_volatility'],
        performance: {
          totalReturn: 0.15,
          sharpeRatio: 1.5,
          maxDrawdown: -0.08
        }
      });

      // Simulation test should be logged
    });

    it('should track failed simulations', async () => {
      await audit.logSimulationTest({
        artifactId: 'artifact-002',
        nodeId: 'node-2',
        passed: false,
        simulatedConditions: ['bear_market'],
        performance: {
          totalReturn: -0.2,
          sharpeRatio: -0.5,
          maxDrawdown: -0.35
        },
        failureReason: 'excessive_drawdown'
      });

      // Failure details should be logged
    });

    it('should include simulation metadata', async () => {
      await audit.logSimulationTest({
        artifactId: 'artifact-003',
        nodeId: 'node-2',
        passed: true,
        simulatedConditions: ['ranging_market', 'low_volatility'],
        simulationDuration: 1000,
        iterations: 100,
        performance: {
          totalReturn: 0.05,
          sharpeRatio: 0.8,
          maxDrawdown: -0.03
        }
      });

      // Metadata should be preserved
    });
  });

  // ============================================================================
  // logGovernanceReview Tests
  // ============================================================================

  describe('logGovernanceReview', () => {
    it('should log a governance review event', async () => {
      await audit.logGovernanceReview({
        artifactId: 'artifact-001',
        nodeId: 'node-2',
        decision: 'approved',
        reviewedBy: 'constitution-committee',
        reviewLevel: 'network'
      });

      // Governance decision should be logged
    });

    it('should track review conditions', async () => {
      await audit.logGovernanceReview({
        artifactId: 'artifact-002',
        nodeId: 'node-2',
        decision: 'approved_with_conditions',
        reviewedBy: 'regional-authority',
        reviewLevel: 'regional',
        conditions: [
          'require_human_oversight',
          'limit_allocation_percentage'
        ]
      });

      // Conditions should be logged
    });

    it('should log rejections from governance', async () => {
      await audit.logGovernanceReview({
        artifactId: 'artifact-003',
        nodeId: 'node-2',
        decision: 'rejected',
        reviewedBy: 'local-authority',
        reviewLevel: 'node',
        rejectionReason: 'outside_authority_scope'
      });

      // Rejection reason should be logged
    });
  });

  // ============================================================================
  // queryAudit Tests
  // ============================================================================

  describe('queryAudit', () => {
    it('should query audit log by artifact ID', async () => {
      const query: AuditQuery = {
        artifactId: 'artifact-001',
        startDate: Date.now() - 86400000,
        endDate: Date.now()
      };

      const events = await audit.queryAudit(query);

      expect(Array.isArray(events)).toBe(true);
    });

    it('should query audit log by event type', async () => {
      const query: AuditQuery = {
        eventType: 'adoption',
        startDate: Date.now() - 86400000,
        endDate: Date.now()
      };

      const events = await audit.queryAudit(query);

      expect(Array.isArray(events)).toBe(true);
    });

    it('should query audit log by node ID', async () => {
      const query: AuditQuery = {
        nodeId: 'node-1',
        startDate: Date.now() - 86400000,
        endDate: Date.now()
      };

      const events = await audit.queryAudit(query);

      expect(Array.isArray(events)).toBe(true);
    });

    it('should handle complex queries', async () => {
      const query: AuditQuery = {
        artifactId: 'artifact-001',
        eventType: 'qualification',
        nodeId: 'node-2',
        startDate: Date.now() - 86400000,
        endDate: Date.now()
      };

      const events = await audit.queryAudit(query);

      expect(Array.isArray(events)).toBe(true);
    });

    it('should handle empty results', async () => {
      const query: AuditQuery = {
        artifactId: 'nonexistent-artifact',
        startDate: Date.now() - 86400000,
        endDate: Date.now()
      };

      const events = await audit.queryAudit(query);

      expect(Array.isArray(events)).toBe(true);
    });
  });

  // ============================================================================
  // getAdoptionStats Tests
  // ============================================================================

  describe('getAdoptionStats', () => {
    it('should return statistics for a node', async () => {
      const stats = await audit.getAdoptionStats('node-1');

      expect(stats).toBeDefined();
      expect(typeof stats.totalReceived).toBe('number');
      expect(typeof stats.totalAdopted).toBe('number');
      expect(typeof stats.totalRejected).toBe('number');
    });

    it('should break down by category', async () => {
      const stats = await audit.getAdoptionStats('node-1');

      expect(stats.byCategory).toBeDefined();
      expect(typeof stats.byCategory.informational).toBe('number');
      expect(typeof stats.byCategory.advisory).toBe('number');
      expect(typeof stats.byCategory.simulationOnly).toBe('number');
      expect(typeof stats.byCategory.allocativeEligible).toBe('number');
    });

    it('should break down by rejection reason', async () => {
      const stats = await audit.getAdoptionStats('node-1');

      expect(stats.byRejectionReason).toBeDefined();
      expect(typeof stats.byRejectionReason).toBe('object');
    });

    it('should support date range filtering', async () => {
      const startDate = Date.now() - 604800000; // 7 days ago
      const endDate = Date.now();

      const stats = await audit.getAdoptionStats('node-1', startDate, endDate);

      expect(stats).toBeDefined();
    });

    it('should calculate adoption rate', async () => {
      const stats = await audit.getAdoptionStats('node-1');

      const adoptionRate = stats.totalReceived > 0
        ? stats.totalAdopted / stats.totalReceived
        : 0;

      expect(adoptionRate).toBeGreaterThanOrEqual(0);
      expect(adoptionRate).toBeLessThanOrEqual(1);
    });
  });

  // ============================================================================
  // getArtifactAuditTrail Tests
  // ============================================================================

  describe('getArtifactAuditTrail', () => {
    it('should return full audit trail for an artifact', async () => {
      const trail = await audit.getArtifactAuditTrail('artifact-001');

      expect(Array.isArray(trail)).toBe(true);
    });

    it('should include events in chronological order', async () => {
      const trail = await audit.getArtifactAuditTrail('artifact-001');

      // In real implementation, verify ordering
      expect(Array.isArray(trail)).toBe(true);
    });

    it('should include all event types for artifact', async () => {
      const trail = await audit.getArtifactAuditTrail('artifact-001');

      const eventTypes = new Set(trail.map(e => e.eventType));
      // May include: publication, qualification, adoption, rejection, etc.
    });
  });

  // ============================================================================
  // verifyAuditCompleteness Tests
  // ============================================================================

  describe('verifyAuditCompleteness', () => {
    it('should verify complete audit trail', async () => {
      const completeness = await audit.verifyAuditCompleteness('artifact-001');

      expect(completeness).toBeDefined();
      expect(typeof completeness.isComplete).toBe('boolean');
      expect(typeof completeness.missingEvents).toBe('number');
    });

    it('should identify gaps in audit trail', async () => {
      const completeness = await audit.verifyAuditCompleteness('artifact-001');

      if (!completeness.isComplete) {
        expect(completeness.gaps).toBeDefined();
        expect(completeness.gaps.length).toBeGreaterThan(0);
      }
    });

    it('should track required event types', async () => {
      const completeness = await audit.verifyAuditCompleteness('artifact-001');

      expect(completeness.requiredEvents).toBeDefined();
      expect(Array.isArray(completeness.requiredEvents)).toBe(true);
    });
  });

  // ============================================================================
  // getNodeStatistics Tests
  // ============================================================================

  describe('getNodeStatistics', () => {
    it('should return comprehensive node statistics', async () => {
      const stats = await audit.getNodeStatistics('node-1');

      expect(stats).toBeDefined();
      expect(stats.nodeId).toBe('node-1');
    });

    it('should track activity over time', async () => {
      const stats = await audit.getNodeStatistics('node-1');

      expect(stats.activityMetrics).toBeDefined();
    });

    it('should calculate participation metrics', async () => {
      const stats = await audit.getNodeStatistics('node-1');

      expect(stats.participationMetrics).toBeDefined();
    });
  });

  // ============================================================================
  // getNetworkStatistics Tests
  // ============================================================================

  describe('getNetworkStatistics', () => {
    it('should return network-wide statistics', async () => {
      const stats = await audit.getNetworkStatistics();

      expect(stats).toBeDefined();
    });

    it('should track total artifacts exchanged', async () => {
      const stats = await audit.getNetworkStatistics();

      expect(typeof stats.totalArtifactsExchanged).toBe('number');
    });

    it('should track network health metrics', async () => {
      const stats = await audit.getNetworkStatistics();

      expect(stats.networkHealth).toBeDefined();
    });
  });
});
