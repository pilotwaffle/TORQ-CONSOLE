/**
 * Layer 12: Test Helpers
 *
 * Provides mock repository and test utilities for Layer 12 testing.
 */

import type { ILayer12Repository } from '@/services/layer12/ILayer12Repository';
import type {
  ClaimRecord,
  QualificationResult,
  ContradictionRecord,
  BaseAuditEvent,
  ClaimQuery,
  AuditQuery
} from '@/types/layer12/epistemic';

/**
 * Create a mock repository for testing
 */
export function createMockRepository(): ILayer12Repository {
  const claims = new Map<string, ClaimRecord>();
  const qualifications = new Map<string, QualificationResult[]>();
  const contradictions = new Map<string, ContradictionRecord>();
  const auditEvents = new Map<string, BaseAuditEvent>();

  return {
    // Claim operations
    async createClaim(artifact: any): Promise<ClaimRecord> {
      const record: ClaimRecord = {
        ...artifact,
        receivedAt: Date.now(),
        indexedAt: Date.now()
      };
      claims.set(record.artifactId, record);
      return record;
    },

    async getClaim(claimId: string): Promise<ClaimRecord | null> {
      return claims.get(claimId) || null;
    },

    async queryClaims(query: ClaimQuery): Promise<ClaimRecord[]> {
      let results = Array.from(claims.values());

      if (query.artifactType) {
        results = results.filter(r => r.artifactType === query.artifactType);
      }
      if (query.originNode) {
        results = results.filter(r => r.originNode === query.originNode);
      }
      if (query.domain) {
        results = results.filter(r => r.context.domain === query.domain);
      }
      if (query.missionType) {
        results = results.filter(r => r.context.missionType === query.missionType);
      }
      if (query.agentTopology) {
        results = results.filter(r => r.context.agentTopology === query.agentTopology);
      }
      if (query.minConfidence !== undefined) {
        results = results.filter(r => r.evidence.confidence >= query.minConfidence);
      }
      if (query.allowedUse) {
        results = results.filter(r => r.allowedUses.includes(query.allowedUse));
      }
      if (query.timeRange) {
        results = results.filter(r => r.createdAt >= query.timeRange.start && r.createdAt <= query.timeRange.end);
      }
      if (query.limit) {
        results = results.slice(0, query.limit);
      }

      return results;
    },

    async updateClaimLimitations(claimId: string, limitations: string[]): Promise<void> {
      const claim = claims.get(claimId);
      if (claim) {
        claim.limitations = limitations;
      }
    },

    async deleteClaim(claimId: string): Promise<void> {
      if (!claims.has(claimId)) {
        throw new Error('Claim not found');
      }
      claims.delete(claimId);
    },

    // Qualification operations
    async createQualification(result: QualificationResult): Promise<void> {
      if (!qualifications.has(result.artifactId)) {
        qualifications.set(result.artifactId, []);
      }
      qualifications.get(result.artifactId)!.push(result);
    },

    async getQualifications(artifactId: string): Promise<QualificationResult[]> {
      return qualifications.get(artifactId) || [];
    },

    async getLatestQualification(artifactId: string, nodeId: string): Promise<QualificationResult | null> {
      const quals = qualifications.get(artifactId) || [];
      return quals[quals.length - 1] || null;
    },

    // Contradiction operations
    async createContradiction(record: ContradictionRecord): Promise<void> {
      contradictions.set(record.contradictionId, record);
    },

    async getContradiction(contradictionId: string): Promise<ContradictionRecord | null> {
      return contradictions.get(contradictionId) || null;
    },

    async getContradictions(claimId: string): Promise<ContradictionRecord[]> {
      const results: ContradictionRecord[] = [];
      for (const record of contradictions.values()) {
        if (record.claimAId === claimId || record.claimBId === claimId) {
          results.push(record);
        }
      }
      return results;
    },

    async getContradictionsForClaim(claimId: string): Promise<ContradictionRecord[]> {
      return this.getContradictions(claimId);
    },

    async updateContradictionResolution(
      contradictionId: string,
      resolutionType: string,
      resolutionNotes?: string,
      resolvedBy?: string
    ): Promise<void> {
      const record = contradictions.get(contradictionId);
      if (!record) {
        throw new Error('Contradiction not found');
      }
      record.resolved = true;
      record.resolutionType = resolutionType as any;
      record.resolutionNotes = resolutionNotes;
      record.resolvedBy = resolvedBy;
      record.resolvedAt = Date.now();
    },

    // Audit operations
    async logEvent(event: BaseAuditEvent): Promise<void> {
      auditEvents.set(event.eventId, event);
    },

    async queryAudit(query: AuditQuery): Promise<BaseAuditEvent[]> {
      let results = Array.from(auditEvents.values());

      if (query.artifactId) {
        results = results.filter(e => e.artifactId === query.artifactId);
      }
      if (query.eventType) {
        results = results.filter(e => e.eventType === query.eventType);
      }
      if (query.nodeId) {
        results = results.filter(e => e.nodeId === query.nodeId);
      }
      if (query.startDate !== undefined) {
        results = results.filter(e => e.timestamp >= query.startDate!);
      }
      if (query.endDate !== undefined) {
        results = results.filter(e => e.timestamp <= query.endDate!);
      }

      return results;
    },

    // Adoption operations
    async createAdoption(
      artifactId: string,
      adoptingNode: string,
      adoptionType: 'informational' | 'advisory' | 'simulation_tested' | 'allocative_eligible',
      adaptations?: string[]
    ): Promise<string> {
      return `adoption_${artifactId}_${adoptingNode}_${Date.now()}`;
    },

    async getAdoptions(artifactId: string): Promise<any[]> {
      return [];
    },

    async getAdoptionStats(nodeId: string, startDate?: number, endDate?: number): Promise<{
      totalReceived: number;
      totalAdopted: number;
      totalRejected: number;
      adoptionRate: number;
      byCategory: Record<string, number>;
      byRejectionReason: Record<string, number>;
    }> {
      return {
        totalReceived: 0,
        totalAdopted: 0,
        totalRejected: 0,
        adoptionRate: 0,
        byCategory: {
          informational: 0,
          advisory: 0,
          simulationOnly: 0,
          allocativeEligible: 0
        },
        byRejectionReason: {}
      };
    },

    // Transaction support
    async transaction<T>(callback: (repo: ILayer12Repository) => Promise<T>): Promise<T> {
      return callback(this);
    }
  };
}
