/**
 * Layer 12: Collective Intelligence Exchange
 * Repository Interface for Dependency Injection
 *
 * This interface abstracts the database operations needed by Layer 12 services.
 * Services depend on this interface, not the concrete implementation.
 */

import type {
  EpistemicArtifact,
  ClaimRecord,
  QualificationResult,
  ContradictionRecord,
  LocalContext,
  ClaimQuery,
  AuditQuery,
  BaseAuditEvent
} from '@/types/layer12/epistemic';

/**
 * Layer 12 Repository Interface
 *
 * All Layer 12 services should depend on this interface for database operations.
 * This enables:
 * - Easy testing with mock repositories
 * - Swappable database backends
 * - Clear separation of concerns
 */
export interface ILayer12Repository {
  // ============================================================================
  // Claim Operations
  // ============================================================================

  /**
   * Store a new epistemic claim
   */
  createClaim(artifact: EpistemicArtifact): Promise<ClaimRecord>;

  /**
   * Get a claim by ID
   */
  getClaim(claimId: string): Promise<ClaimRecord | null>;

  /**
   * Query claims with filters
   */
  queryClaims(query: ClaimQuery): Promise<ClaimRecord[]>;

  /**
   * Update a claim's limitations
   */
  updateClaimLimitations(claimId: string, limitations: string[]): Promise<void>;

  /**
   * Soft delete a claim
   */
  deleteClaim(claimId: string): Promise<void>;

  // ============================================================================
  // Qualification Operations
  // ============================================================================

  /**
   * Store a qualification result
   */
  createQualification(result: QualificationResult): Promise<void>;

  /**
   * Get all qualifications for an artifact
   */
  getQualifications(artifactId: string): Promise<QualificationResult[]>;

  /**
   * Get the latest qualification by a node for an artifact
   */
  getLatestQualification(artifactId: string, nodeId: string): Promise<QualificationResult | null>;

  // ============================================================================
  // Contradiction Operations
  // ============================================================================

  /**
   * Store a contradiction record
   */
  createContradiction(record: ContradictionRecord): Promise<void>;

  /**
   * Get a contradiction by ID
   */
  getContradiction(contradictionId: string): Promise<ContradictionRecord | null>;

  /**
   * Get all contradictions for a claim
   */
  getContradictionsForClaim(claimId: string): Promise<ContradictionRecord[]>;

  /**
   * Update contradiction resolution
   */
  updateContradictionResolution(
    contradictionId: string,
    resolutionType: string,
    resolutionNotes?: string,
    resolvedBy?: string
  ): Promise<void>;

  // ============================================================================
  // Adoption Operations
  // ============================================================================

  /**
   * Record an artifact adoption
   */
  createAdoption(
    artifactId: string,
    adoptingNode: string,
    adoptionType: 'informational' | 'advisory' | 'simulation_tested' | 'allocative_eligible',
    adaptations?: string[]
  ): Promise<string>;

  /**
   * Get all adoptions for an artifact
   */
  getAdoptions(artifactId: string): Promise<any[]>;

  /**
   * Get adoption statistics for a node
   */
  getAdoptionStats(nodeId: string, startDate?: number, endDate?: number): Promise<{
    totalReceived: number;
    totalAdopted: number;
    totalRejected: number;
    adoptionRate: number;
    byCategory: Record<string, number>;
    byRejectionReason: Record<string, number>;
  }>;

  // ============================================================================
  // Audit Operations
  // ============================================================================

  /**
   * Log an audit event
   */
  logEvent(event: BaseAuditEvent): Promise<void>;

  /**
   * Query audit log
   */
  queryAudit(query: AuditQuery): Promise<BaseAuditEvent[]>;

  // ============================================================================
  // Batch Operations
  // ============================================================================

  /**
   * Execute multiple operations in a transaction
   */
  transaction<T>(callback: (repo: ILayer12Repository) => Promise<T>): Promise<T>;
}
