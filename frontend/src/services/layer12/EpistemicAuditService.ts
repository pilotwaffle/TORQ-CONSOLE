/**
 * Layer 12: Collective Intelligence Exchange
 * EpistemicAuditService
 *
 * Tracks the knowledge network: what was shared, what was adopted,
 * what was rejected, and why. This creates the institutional memory
 * of knowledge exchange and adoption decisions.
 */

import { v4 as uuidv4 } from 'uuid';
import type {
  BaseAuditEvent,
  PublicationEvent,
  QualificationEvent,
  AdoptionEvent,
  RejectionEvent,
  SimulationTestEvent,
  GovernanceReviewEvent,
  AuditQuery,
  AuditEventType,
  AdoptionStatistics,
  EpistemicArtifact
} from '@/types/layer12/epistemic';

/**
 * Audit record stored in the audit log
 */
type AuditEvent =
  | PublicationEvent
  | QualificationEvent
  | AdoptionEvent
  | RejectionEvent
  | SimulationTestEvent
  | GovernanceReviewEvent;

/**
 * Service for tracking epistemic exchange and adoption
 */
export class EpistemicAuditService {
  private auditLog: Map<string, AuditEvent> = new Map();
  private artifactIndex: Map<string, Set<string>> = new Map(); // artifactId -> event IDs
  private nodeIndex: Map<string, Set<string>> = new Map(); // nodeId -> event IDs
  private typeIndex: Map<AuditEventType, Set<string>> = new Map(); // eventType -> event IDs

  constructor() {
    this.initializeIndexes();
  }

  /**
   * Log artifact publication
   */
  async logPublication(event: Omit<PublicationEvent, 'eventId' | 'eventType' | 'timestamp'>): Promise<void> {
    const auditEvent: PublicationEvent = {
      eventId: `audit_${uuidv4()}`,
      eventType: 'publication',
      artifactId: event.artifactId,
      nodeId: event.originNode,
      timestamp: Date.now(),
      originNode: event.originNode,
      artifactType: event.artifactType,
      allowedUses: event.allowedUses
    };

    await this.addEvent(auditEvent);
  }

  /**
   * Log qualification result
   */
  async logQualification(event: Omit<QualificationEvent, 'eventId' | 'eventType' | 'timestamp'>): Promise<void> {
    const auditEvent: QualificationEvent = {
      eventId: `audit_${uuidv4()}`,
      eventType: 'qualification',
      artifactId: event.artifactId,
      nodeId: event.nodeId,
      timestamp: Date.now(),
      category: event.category,
      localRelevance: event.localRelevance,
      localTrust: event.localTrust,
      suggestedAction: event.suggestedAction
    };

    await this.addEvent(auditEvent);
  }

  /**
   * Log adoption decision
   */
  async logAdoption(event: Omit<AdoptionEvent, 'eventId' | 'eventType' | 'timestamp'>): Promise<void> {
    const auditEvent: AdoptionEvent = {
      eventId: `audit_${uuidv4()}`,
      eventType: 'adoption',
      artifactId: event.artifactId,
      nodeId: event.nodeId,
      timestamp: Date.now(),
      adoptionType: event.adoptionType,
      adaptations: event.adaptations
    };

    await this.addEvent(auditEvent);
  }

  /**
   * Log rejection with reason
   */
  async logRejection(event: Omit<RejectionEvent, 'eventId' | 'eventType' | 'timestamp'>): Promise<void> {
    const auditEvent: RejectionEvent = {
      eventId: `audit_${uuidv4()}`,
      eventType: 'rejection',
      artifactId: event.artifactId,
      nodeId: event.nodeId,
      timestamp: Date.now(),
      reason: event.reason,
      details: event.details
    };

    await this.addEvent(auditEvent);
  }

  /**
   * Log simulation test
   */
  async logSimulationTest(event: Omit<SimulationTestEvent, 'eventId' | 'eventType' | 'timestamp'>): Promise<void> {
    const auditEvent: SimulationTestEvent = {
      eventId: `audit_${uuidv4()}`,
      eventType: 'simulation_test',
      artifactId: event.artifactId,
      nodeId: event.nodeId,
      timestamp: Date.now(),
      simulationId: event.simulationId,
      result: event.result
    };

    await this.addEvent(auditEvent);
  }

  /**
   * Log governance review
   */
  async logGovernanceReview(event: Omit<GovernanceReviewEvent, 'eventId' | 'eventType' | 'timestamp'>): Promise<void> {
    const auditEvent: GovernanceReviewEvent = {
      eventId: `audit_${uuidv4()}`,
      eventType: 'governance_review',
      artifactId: event.artifactId,
      nodeId: event.nodeId,
      timestamp: Date.now(),
      reviewId: event.reviewId,
      outcome: event.outcome
    };

    await this.addEvent(auditEvent);
  }

  /**
   * Query audit log
   */
  async queryAudit(query: AuditQuery): Promise<AuditEvent[]> {
    let results = Array.from(this.auditLog.values());

    // Filter by artifact ID
    if (query.artifactId) {
      const eventIds = this.artifactIndex.get(query.artifactId);
      if (eventIds) {
        results = results.filter(r => eventIds.has(r.eventId));
      } else {
        return [];
      }
    }

    // Filter by event type
    if (query.eventType) {
      const eventIds = this.typeIndex.get(query.eventType);
      if (eventIds) {
        results = results.filter(r => eventIds.has(r.eventId));
      } else {
        return [];
      }
    }

    // Filter by node ID
    if (query.nodeId) {
      const eventIds = this.nodeIndex.get(query.nodeId);
      if (eventIds) {
        results = results.filter(r => eventIds.has(r.eventId));
      } else {
        return [];
      }
    }

    // Filter by time range
    if (query.startDate !== undefined) {
      results = results.filter(r => r.timestamp >= query.startDate!);
    }
    if (query.endDate !== undefined) {
      results = results.filter(r => r.timestamp <= query.endDate!);
    }

    // Sort by timestamp descending
    results.sort((a, b) => b.timestamp - a.timestamp);

    return results;
  }

  /**
   * Get adoption statistics for a time period
   */
  async getAdoptionStats(
    nodeId: string,
    startDate?: number,
    endDate?: number
  ): Promise<AdoptionStatistics> {
    const events = await this.queryAudit({
      nodeId,
      startDate,
      endDate
    });

    const totalReceived = new Set<string>();
    let totalAdopted = 0;
    let totalRejected = 0;
    const byCategory = {
      informational: 0,
      advisory: 0,
      simulationOnly: 0,
      allocativeEligible: 0
    };
    const byRejectionReason: Record<string, number> = {};

    for (const event of events) {
      // Track unique artifacts received
      totalReceived.add(event.artifactId);

      if (event.eventType === 'adoption') {
        totalAdopted++;
        const adoptionEvent = event as AdoptionEvent;
        switch (adoptionEvent.adoptionType) {
          case 'informational':
            byCategory.informational++;
            break;
          case 'advisory':
            byCategory.advisory++;
            break;
          case 'simulation_tested':
            byCategory.simulationOnly++;
            break;
          case 'allocative_eligible':
            byCategory.allocativeEligible++;
            break;
        }
      } else if (event.eventType === 'rejection') {
        totalRejected++;
        const rejectionEvent = event as RejectionEvent;
        byRejectionReason[rejectionEvent.reason] = (byRejectionReason[rejectionEvent.reason] || 0) + 1;
      }
    }

    const adoptionRate = totalReceived.size > 0 ? totalAdopted / totalReceived.size : 0;

    return {
      totalReceived: totalReceived.size,
      totalAdopted,
      totalRejected,
      adoptionRate,
      byCategory,
      byRejectionReason
    };
  }

  /**
   * Get audit trail for a specific artifact
   */
  async getArtifactAuditTrail(artifactId: string): Promise<{
    artifactId: string;
    events: Array<{
      eventType: AuditEventType;
      timestamp: number;
      nodeId: string;
      details: unknown;
    }>;
  }> {
    const events = await this.queryAudit({ artifactId });

    return {
      artifactId,
      events: events.map(e => ({
        eventType: e.eventType,
        timestamp: e.timestamp,
        nodeId: e.nodeId,
        details: this.extractDetails(e)
      }))
    };
  }

  /**
   * Get statistics for a node
   */
  async getNodeStatistics(nodeId: string): Promise<{
    totalEvents: number;
    eventsByType: Record<AuditEventType, number>;
    artifactsReceived: number;
    artifactsAdopted: number;
    artifactsRejected: number;
    mostActivePeriod: { date: string; count: number };
  }> {
    const events = await this.queryAudit({ nodeId });

    const eventsByType: Record<AuditEventType, number> = {
      publication: 0,
      qualification: 0,
      adoption: 0,
      rejection: 0,
      simulation_test: 0,
      governance_review: 0
    };

    const artifactsReceived = new Set<string>();
    let artifactsAdopted = 0;
    let artifactsRejected = 0;

    // Activity by date
    const activityByDate: Map<string, number> = new Map();

    for (const event of events) {
      eventsByType[event.eventType]++;

      if (event.eventType === 'qualification') {
        artifactsReceived.add(event.artifactId);
      } else if (event.eventType === 'adoption') {
        artifactsAdopted++;
      } else if (event.eventType === 'rejection') {
        artifactsRejected++;
      }

      // Track activity by date
      const date = new Date(event.timestamp).toISOString().split('T')[0];
      activityByDate.set(date, (activityByDate.get(date) || 0) + 1);
    }

    // Find most active period
    let mostActivePeriod = { date: '', count: 0 };
    for (const [date, count] of activityByDate.entries()) {
      if (count > mostActivePeriod.count) {
        mostActivePeriod = { date, count };
      }
    }

    return {
      totalEvents: events.length,
      eventsByType,
      artifactsReceived: artifactsReceived.size,
      artifactsAdopted,
      artifactsRejected,
      mostActivePeriod
    };
  }

  /**
   * Verify audit completeness for an artifact
   */
  async verifyAuditCompleteness(artifactId: string): Promise<{
    complete: boolean;
    missingEvents: AuditEventType[];
    existingEvents: AuditEventType[];
  }> {
    const events = await this.queryAudit({ artifactId });
    const existingEvents = new Set(events.map(e => e.eventType));

    // Determine which events should be present based on the artifact lifecycle
    const expectedEvents: AuditEventType[] = [];

    if (existingEvents.has('publication')) {
      expectedEvents.push('publication');
      // After publication, qualification should occur
      if (!existingEvents.has('qualification')) {
        expectedEvents.push('qualification');
      }
    }

    // After qualification, adoption or rejection should occur
    if (existingEvents.has('qualification')) {
      if (!existingEvents.has('adoption') && !existingEvents.has('rejection')) {
        expectedEvents.push('adoption', 'rejection');
      }
    }

    // If suggested_action was simulation, simulation_test should exist
    const qualEvent = events.find(e => e.eventType === 'qualification') as QualificationEvent;
    if (qualEvent?.suggestedAction === 'send_to_simulation') {
      if (!existingEvents.has('simulation_test')) {
        expectedEvents.push('simulation_test');
      }
    }

    // If suggested_action was governance, governance_review should exist
    if (qualEvent?.suggestedAction === 'send_to_governance') {
      if (!existingEvents.has('governance_review')) {
        expectedEvents.push('governance_review');
      }
    }

    const missingEvents: AuditEventType[] = [];
    for (const expected of expectedEvents) {
      if (!existingEvents.has(expected)) {
        missingEvents.push(expected);
      }
    }

    return {
      complete: missingEvents.length === 0,
      missingEvents,
      existingEvents: Array.from(existingEvents)
    };
  }

  /**
   * Add event to audit log
   */
  private async addEvent(event: AuditEvent): Promise<void> {
    this.auditLog.set(event.eventId, event);

    // Update indexes
    if (!this.artifactIndex.has(event.artifactId)) {
      this.artifactIndex.set(event.artifactId, new Set());
    }
    this.artifactIndex.get(event.artifactId)!.add(event.eventId);

    if (!this.nodeIndex.has(event.nodeId)) {
      this.nodeIndex.set(event.nodeId, new Set());
    }
    this.nodeIndex.get(event.nodeId)!.add(event.eventId);

    if (!this.typeIndex.has(event.eventType)) {
      this.typeIndex.set(event.eventType, new Set());
    }
    this.typeIndex.get(event.eventType)!.add(event.eventId);

    // Persist to storage
    await this.persistEvent(event);
  }

  /**
   * Extract details from an audit event
   */
  private extractDetails(event: AuditEvent): unknown {
    switch (event.eventType) {
      case 'publication':
        return {
          originNode: (event as PublicationEvent).originNode,
          artifactType: (event as PublicationEvent).artifactType,
          allowedUses: (event as PublicationEvent).allowedUses
        };
      case 'qualification':
        return {
          category: (event as QualificationEvent).category,
          localRelevance: (event as QualificationEvent).localRelevance,
          localTrust: (event as QualificationEvent).localTrust,
          suggestedAction: (event as QualificationEvent).suggestedAction
        };
      case 'adoption':
        return {
          adoptionType: (event as AdoptionEvent).adoptionType,
          adaptations: (event as AdoptionEvent).adaptations
        };
      case 'rejection':
        return {
          reason: (event as RejectionEvent).reason,
          details: (event as RejectionEvent).details
        };
      case 'simulation_test':
        return {
          simulationId: (event as SimulationTestEvent).simulationId,
          result: (event as SimulationTestEvent).result
        };
      case 'governance_review':
        return {
          reviewId: (event as GovernanceReviewEvent).reviewId,
          outcome: (event as GovernanceReviewEvent).outcome
        };
    }
  }

  /**
   * Initialize indexes
   */
  private initializeIndexes(): void {
    this.artifactIndex = new Map();
    this.nodeIndex = new Map();
    this.typeIndex = new Map();
  }

  /**
   * Persist event to storage
   */
  private async persistEvent(event: AuditEvent): Promise<void> {
    // TODO: Integrate with database layer
    console.log(`[L12] Persisting audit event: ${event.eventId} (${event.eventType})`);
  }
}

/**
 * Export singleton instance factory
 */
export function createEpistemicAuditService(): EpistemicAuditService {
  return new EpistemicAuditService();
}
