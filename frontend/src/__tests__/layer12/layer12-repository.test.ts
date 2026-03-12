/**
 * Layer 12: Collective Intelligence Exchange
 * Unit Tests - Database Repository
 *
 * Tests the Layer12DBRepository class with mock database client.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { Layer12DBRepository, createLayer12Repository } from '@/lib/db/layer12-repository';
import type { EpistemicArtifact, LocalContext } from '@/types/layer12/epistemic';

// Mock database client
class MockDBClient {
  public query = vi.fn();
  public exec = vi.fn();
  public transaction = vi.fn();
}

describe('Layer12DBRepository', () => {
  let mockDb: MockDBClient;
  let repository: Layer12DBRepository;

  beforeEach(() => {
    mockDb = new MockDBClient();
    repository = new Layer12DBRepository(mockDb as any);
    vi.clearAllMocks();
  });

  // ============================================================================
  // Claim Tests
  // ============================================================================

  describe('createClaim', () => {
    it('should insert a claim and return the record', async () => {
      const artifact: EpistemicArtifact = {
        artifactId: 'test-claim-001',
        artifactType: 'observational',
        originNode: 'node-1',
        originLayer: 4,
        createdAt: Date.now(),
        version: '1.0.0',
        claim: 'Test claim',
        summary: 'Test summary',
        context: {
          domain: 'testing',
          missionType: 'unit-test',
          agentTopology: 'single'
        },
        evidence: {
          confidence: 0.9,
          sources: [],
          sampleSize: 0,
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

      const mockRow = {
        claim_id: 'test-claim-001',
        artifact_type: 'observational',
        origin_node: 'node-1',
        origin_layer: 4,
        created_at: artifact.createdAt,
        version: '1.0.0',
        claim: 'Test claim',
        summary: 'Test summary',
        context_json: JSON.stringify(artifact.context),
        evidence_json: JSON.stringify(artifact.evidence),
        limitations_json: JSON.stringify([]),
        allowed_uses_json: JSON.stringify(['informational']),
        provenance_json: JSON.stringify(artifact.provenance),
        received_at: Date.now(),
        indexed_at: Date.now()
      };

      mockDb.query.mockResolvedValue([mockRow]);

      const result = await repository.createClaim(artifact);

      expect(result).toBeDefined();
      expect(result.artifactId).toBe('test-claim-001');
      expect(result.claim).toBe('Test claim');
      expect(mockDb.query).toHaveBeenCalled();
    });

    it('should throw error when database returns no rows', async () => {
      const artifact: EpistemicArtifact = {
        artifactId: 'test-claim-002',
        artifactType: 'observational',
        originNode: 'node-1',
        originLayer: 4,
        createdAt: Date.now(),
        version: '1.0.0',
        claim: 'Test claim',
        summary: 'Test summary',
        context: {
          domain: 'testing',
          missionType: 'unit-test',
          agentTopology: 'single'
        },
        evidence: {
          confidence: 0.9,
          sources: [],
          sampleSize: 0,
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

      mockDb.query.mockResolvedValue([]);

      await expect(repository.createClaim(artifact)).rejects.toThrow('Failed to create claim');
    });
  });

  describe('getClaim', () => {
    it('should retrieve a claim by ID', async () => {
      const mockRow = {
        claim_id: 'test-claim-001',
        artifact_type: 'observational',
        origin_node: 'node-1',
        origin_layer: 4,
        created_at: Date.now(),
        version: '1.0.0',
        claim: 'Test claim',
        summary: 'Test summary',
        context_json: JSON.stringify({ domain: 'testing' }),
        evidence_json: JSON.stringify({ confidence: 0.9 }),
        limitations_json: JSON.stringify([]),
        allowed_uses_json: JSON.stringify(['informational']),
        provenance_json: JSON.stringify({ sourceNode: 'node-1' }),
        received_at: Date.now(),
        indexed_at: Date.now()
      };

      mockDb.query.mockResolvedValue([mockRow]);

      const result = await repository.getClaim('test-claim-001');

      expect(result).toBeDefined();
      expect(result?.artifactId).toBe('test-claim-001');
    });

    it('should return null when claim not found', async () => {
      mockDb.query.mockResolvedValue([]);

      const result = await repository.getClaim('nonexistent');

      expect(result).toBeNull();
    });
  });

  describe('queryClaims', () => {
    it('should query claims with filters', async () => {
      const mockRows = [
        {
          claim_id: 'claim-001',
          artifact_type: 'pattern',
          origin_node: 'node-1',
          origin_layer: 4,
          created_at: Date.now(),
          version: '1.0.0',
          claim: 'Pattern claim',
          summary: 'Pattern summary',
          context_json: JSON.stringify({ domain: 'trading' }),
          evidence_json: JSON.stringify({ confidence: 0.8 }),
          limitations_json: JSON.stringify([]),
          allowed_uses_json: JSON.stringify(['advisory']),
          provenance_json: JSON.stringify({ sourceNode: 'node-1' }),
          received_at: Date.now(),
          indexed_at: Date.now()
        }
      ];

      mockDb.query.mockResolvedValue(mockRows);

      const result = await repository.queryClaims({
        artifactType: 'pattern',
        domain: 'trading',
        limit: 10
      });

      expect(result).toHaveLength(1);
      expect(result[0].artifactType).toBe('pattern');
    });

    it('should handle empty query results', async () => {
      mockDb.query.mockResolvedValue([]);

      const result = await repository.queryClaims({});

      expect(result).toHaveLength(0);
    });
  });

  // ============================================================================
  // Contradiction Tests
  // ============================================================================

  describe('createContradiction', () => {
    it('should register a contradiction between two claims', async () => {
      const mockRow = {
        contradiction_id: 'contradiction_001',
        claim_a_id: 'claim-001',
        claim_b_id: 'claim-002',
        contradiction_type: 'direct_contradiction',
        detected_at: Date.now(),
        detected_by: 'node-1',
        resolved: false,
        resolution_type: null,
        resolution_notes: null,
        resolved_at: null,
        resolved_by: null
      };

      mockDb.query.mockResolvedValue([mockRow]);

      const result = await repository.createContradiction(
        'claim-001',
        'claim-002',
        'direct_contradiction',
        'node-1'
      );

      expect(result).toBeDefined();
      expect(result.contradictionId).toBe('contradiction_001');
      expect(result.claimAId).toBe('claim-001');
      expect(result.claimBId).toBe('claim-002');
      expect(result.contradictionType).toBe('direct_contradiction');
    });
  });

  describe('getContradictions', () => {
    it('should retrieve contradictions for a claim', async () => {
      const mockRows = [
        {
          contradiction_id: 'contradiction_001',
          claim_a_id: 'claim-001',
          claim_b_id: 'claim-002',
          contradiction_type: 'direct_contradiction',
          detected_at: Date.now(),
          detected_by: 'node-1',
          resolved: false,
          resolution_type: null,
          resolution_notes: null,
          resolved_at: null,
          resolved_by: null
        }
      ];

      mockDb.query.mockResolvedValue(mockRows);

      const result = await repository.getContradictions('claim-001');

      expect(result).toHaveLength(1);
      expect(result[0].claimAId).toBe('claim-001');
    });
  });

  describe('resolveContradiction', () => {
    it('should mark a contradiction as resolved', async () => {
      mockDb.exec.mockResolvedValue({ rowsAffected: 1 });

      const result = await repository.resolveContradiction(
        'contradiction_001',
        'a_is_correct',
        'Evidence supports claim A'
      );

      expect(result).toBe(true);
      expect(mockDb.exec).toHaveBeenCalled();
    });

    it('should return false when contradiction not found', async () => {
      mockDb.exec.mockResolvedValue({ rowsAffected: 0 });

      const result = await repository.resolveContradiction(
        'nonexistent',
        'a_is_correct'
      );

      expect(result).toBe(false);
    });
  });

  // ============================================================================
  // Qualification Tests
  // ============================================================================

  describe('createQualification', () => {
    it('should store a qualification result', async () => {
      const mockRow = {
        qualification_id: 'qual-001',
        artifact_id: 'claim-001',
        qualifying_node: 'node-2',
        qualified_at: Date.now(),
        category: 'high_confidence',
        local_relevance: 0.9,
        provenance_strength: 0.8,
        confidence_stability: 0.85,
        overall_trust: 0.85,
        has_context_clash: false,
        has_contradictions: false,
        requires_simulation: false,
        policy_compatible: true,
        context_comparison_json: '{}',
        recommended_uses_json: '["advisory"]',
        warnings_json: '[]',
        adaptations_json: '[]',
        suggested_action: 'use_advisory'
      };

      mockDb.query.mockResolvedValue([mockRow]);

      const result = await repository.createQualification(
        'claim-001',
        'node-2',
        {
          category: 'high_confidence',
          localRelevance: 0.9,
          provenanceStrength: 0.8,
          confidenceStability: 0.85,
          overallTrust: 0.85,
          hasContextClash: false,
          hasContradictions: false,
          requiresSimulation: false,
          policyCompatible: true,
          contextComparison: {},
          recommendedUses: ['advisory'],
          warnings: [],
          adaptations: [],
          suggestedAction: 'use_advisory'
        }
      );

      expect(result).toBe('qual-001');
    });
  });

  // ============================================================================
  // Audit Tests
  // ============================================================================

  describe('logEvent', () => {
    it('should log an audit event', async () => {
      mockDb.exec.mockResolvedValue({ rowsAffected: 1 });

      await repository.logEvent({
        eventId: 'event-001',
        eventType: 'publication',
        artifactId: 'claim-001',
        nodeId: 'node-1',
        eventData: { test: 'data' }
      });

      expect(mockDb.exec).toHaveBeenCalled();
    });
  });

  describe('queryAudit', () => {
    it('should query audit log with filters', async () => {
      const mockRows = [
        {
          event_id: 'event-001',
          event_type: 'publication',
          artifact_id: 'claim-001',
          node_id: 'node-1',
          timestamp: Date.now(),
          event_data_json: '{"test": "data"}',
          adoption_outcome: null,
          rejection_reason: null,
          governance_decision: null
        }
      ];

      mockDb.query.mockResolvedValue(mockRows);

      const result = await repository.queryAudit({
        artifactId: 'claim-001',
        eventType: 'publication'
      });

      expect(result).toHaveLength(1);
      // queryAudit returns raw database rows with snake_case
      expect(result[0].artifact_id).toBe('claim-001');
    });
  });

  // ============================================================================
  // Adoption Tests
  // ============================================================================

  describe('createAdoption', () => {
    it('should record an artifact adoption', async () => {
      const mockRow = {
        adoption_id: 'adoption-001',
        artifact_id: 'claim-001',
        adopting_node: 'node-2',
        adopted_at: Date.now(),
        adoption_type: 'advisory',
        adaptations_json: '[]',
        usage_count: 0
      };

      mockDb.query.mockResolvedValue([mockRow]);

      const result = await repository.createAdoption(
        'claim-001',
        'node-2',
        'advisory'
      );

      expect(result).toBe('adoption-001');
    });
  });

  describe('getAdoptions', () => {
    it('should retrieve adoptions for an artifact', async () => {
      const mockRows = [
        {
          adoption_id: 'adoption-001',
          artifact_id: 'claim-001',
          adopting_node: 'node-2',
          adopted_at: Date.now(),
          adoption_type: 'advisory',
          adaptations_json: '[]',
          usage_count: 5,
          superseded_by: null
        }
      ];

      mockDb.query.mockResolvedValue(mockRows);

      const result = await repository.getAdoptions('claim-001');

      expect(result).toHaveLength(1);
      // getAdoptions returns raw database rows with snake_case
      expect(result[0].adopting_node).toBe('node-2');
    });
  });

  // ============================================================================
  // Statistics Tests
  // ============================================================================

  describe('getAdoptionStats', () => {
    it('should return adoption statistics for a node', async () => {
      const mockStatsRow = {
        total_received: 10,
        total_adopted: 7,
        total_rejected: 2
      };

      const mockCategoryRows = [
        { adoption_outcome: 'informational', count: 2 },
        { adoption_outcome: 'advisory', count: 3 },
        { adoption_outcome: 'allocativeEligible', count: 2 }
      ];

      const mockRejectionRows = [
        { rejection_reason: 'context_mismatch', count: 1 },
        { rejection_reason: 'low_confidence', count: 1 }
      ];

      mockDb.query
        .mockResolvedValueOnce([mockStatsRow])
        .mockResolvedValueOnce(mockCategoryRows)
        .mockResolvedValueOnce(mockRejectionRows);

      const result = await repository.getAdoptionStats('node-1');

      expect(result.totalReceived).toBe(10);
      expect(result.totalAdopted).toBe(7);
      expect(result.totalRejected).toBe(2);
      expect(result.byCategory).toBeDefined();
      expect(result.byRejectionReason).toBeDefined();
    });
  });

  // ============================================================================
  // Factory Function Tests
  // ============================================================================

  describe('createLayer12Repository', () => {
    it('should create a repository instance', () => {
      const repo = createLayer12Repository(mockDb as any);

      expect(repo).toBeInstanceOf(Layer12DBRepository);
    });
  });
});
