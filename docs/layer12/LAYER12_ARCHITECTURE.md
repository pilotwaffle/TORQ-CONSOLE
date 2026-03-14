# Layer 12 Architecture
## TORQ Federation System

**Layer 12: Multi-Node Federation**
**Version:** 0.12.2b
**Status:** COMPLETE

---

## Overview

Layer 12 provides distributed reasoning and federated claim validation for the TORQ system. It enables multiple nodes to collaborate on knowledge validation while detecting and containing various attack vectors.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TORQ Layer 12 Federation                          │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    InboundFederatedClaimProcessor                  │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │                    Safeguards Pipeline                        │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │   │   │
│  │  │  │Eligi-    │ │Similar-  │ │Plurality│ │Allocative    │  │   │   │
│  │  │  │bility    │ │ity       │ │Preserva-│ │Boundaries    │  │   │   │
│  │  │  │Filter    │ │Engine    │ │tion     │ │Guard         │  │   │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │                    Trust Evaluation                           │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │   │   │
│  │  │  │Identity  │ │Signature│ │Trust     │                    │   │   │
│  │  │  │Guard     │ │Verify    │ │Decision  │                    │   │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘                    │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │                    Persistence                                │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │   │   │
│  │  │  │Claim     │ │Audit     │ │Duplicate │                    │   │   │
│  │  │  │Registry  │ │Log       │ │Suppress- │                    │   │   │
│  │  │  │          │ │          │ │ion       │                    │   │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘                    │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Simulation & Validation                          │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐      │   │
│  │  │ Network      │  │ Event        │  │ Calibrated Claim     │      │   │
│  │  │ Controller   │  │ Scheduler    │  │ Generator            │      │   │
│  │  │              │  │              │  │                      │      │   │
│  │  │ - Topology   │  │ - Priority   │  │ - Quality Bias       │      │   │
│  │  │ - Nodes      │  │ - Batching   │  │ - Domain Awareness    │      │   │
│  │  │ - Epochs     │  │ - Async      │  │ - Stance Randomness   │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘      │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐      │   │
│  │  │ Node         │  │ Network      │  │ Scenario             │      │   │
│  │  │ Registry     │  │ Metrics      │  │ Definitions          │      │   │
│  │  │              │  │ Engine       │  │                      │      │   │
│  │  │ - Trust Mgmt │  │ - Density    │  │ - Baseline           │      │   │
│  │  │ - Domains    │  │ - Clustering │  │ - Domain Capture     │      │   │
│  │  │ - Profiles   │  │ - Resilience │  │ - Trust Cascade      │      │   │
│  │  │              │  │ - Centrality│  │ - Coalition          │      │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. InboundFederatedClaimProcessor

**Purpose:** Main entry point for processing federated claims

**Location:** `torq_console/layer12/federation/inbound_claim_processor.py`

**Key Responsibilities:**
- Coordinate the safeguards pipeline
- Execute trust evaluation
- Manage claim persistence
- Generate audit logs

**Methods:**
- `process_claim()` - Main processing pipeline
- `process_claim_batch()` - Batch processing for efficiency

---

### 2. FederationIdentityGuard

**Purpose:** Validate node identity and make trust decisions

**Location:** `torq_console/layer12/federation/federation_identity_guard.py`

**Key Responsibilities:**
- Node identity verification
- Signature validation
- Trust score management
- Trust decision logic (accept/quarantine/reject)

**Trust Thresholds:**
- Accept: >= 0.75
- Quarantine: 0.45 - 0.74
- Reject: < 0.45

---

### 3. FederationEligibilityFilter

**Purpose:** Filter low-quality claims before trust evaluation

**Location:** `torq_console/layer12/federation/safeguards/federation_eligibility_filter.py`

**Key Responsibilities:**
- Content quality validation (confidence, provenance, length)
- Rate limiting per node
- Spam detection
- Similarity checking (optional, disabled in simulation)

**Quality Thresholds:**
- Minimum confidence: 0.3
- Minimum provenance: 0.5
- Minimum claim length: 20 characters

---

### 4. NetworkController (Phase 2B)

**Purpose:** Orchestrate multi-node federation simulation

**Location:** `torq_console/layer12/federation/simulator/network/network_controller.py`

**Key Responsibilities:**
- Node lifecycle management
- Topology configuration
- Event-driven simulation epochs
- Claim routing through real processor

**Supported Topologies:**
- `SMALL_WORLD` - Watts-Strogatz model
- `HUB_AND_SPOKE` - Central hub with spoke nodes
- `RANDOM_GRAPH` - Erdos-Renyi model
- `SCALE_FREE` - Power-law degree distribution
- `LINEAR` - Chain topology
- `FULLY_CONNECTED` - All-to-all

---

### 5. EventScheduler (Phase 2B)

**Purpose:** Priority-based asynchronous event scheduling

**Location:** `torq_console/layer12/federation/simulator/network/event_scheduler.py`

**Key Responsibilities:**
- Priority queue management (0-10)
- Event batching for performance
- Handler registration
- Pending count tracking

---

### 6. NodeRegistry (Phase 2B)

**Purpose:** Manage simulated network nodes

**Location:** `torq_console/layer12/federation/simulator/network/node_registry.py`

**Key Responsibilities:**
- Node registration and lifecycle
- Trust state management
- Domain specialization tracking
- Network neighbor management

---

### 7. NetworkMetricsEngine (Phase 2B)

**Purpose:** Calculate network-scale metrics

**Location:** `torq_console/layer12/federation/simulator/network/network_metrics.py`

**Metrics Calculated:**
- Network density
- Average clustering coefficient
- Average path length
- Network resilience score
- Domain competition index
- Gini coefficient (inequality)
- Herfindahl index (concentration)
- Top node concentration

---

### 8. CalibratedClaimGenerator (Phase 2B)

**Purpose:** Generate claims with calibrated quality

**Location:** `torq_console/layer12/federation/simulator/network/claim_generator.py`

**Key Features:**
- Quality bias parameter (0.5-0.95)
- Domain-aware content
- Stance-randomized claims
- Confidence and provenance calibration

**Quality vs Acceptance Mapping:**
- 0.50: Very low quality (~0-5% acceptance)
- 0.60: Low quality (~5-15% acceptance)
- 0.70: Medium-low quality (~15-30% acceptance)
- 0.75: Medium quality (~25-45% acceptance) ⭐ RECOMMENDED
- 0.80: High quality (~40-60% acceptance)
- 0.90: Very high quality (~60-80% acceptance)

---

### 9. Scenario Definitions (Phase 2B)

**Purpose:** Predefined simulation scenarios

**Location:** `torq_console/layer12/federation/simulator/network/scenarios.py`

**Scenarios:**
- `BASELINE` - Standard 10-node small-world
- `NETWORK_GROWTH` - Dynamic node addition
- `DOMAIN_CAPTURE` - Authority concentration testing
- `TRUST_CASCADE_FAILURE` - Trust amplification attack
- `CONTRADICTION_FRAGMENTATION` - Semantic divergence
- `MULTI_NODE_ADVERSARIAL_COALITION` - Coordinated manipulation

---

## Data Models

### FederatedClaimEnvelope

```python
class FederatedClaimEnvelope(BaseModel):
    envelope_id: str
    artifact: FederatedArtifactPayload
    source_node_id: str
    timestamp: datetime
    signature: Optional[str]
    metadata: Dict[str, Any]
```

### InboundProcessingResult

```python
class InboundProcessingResult(BaseModel):
    status: Literal["accepted", "quarantined", "rejected"]
    envelope_id: str
    claim_id: Optional[str]
    source_node_id: str
    effective_trust: float
    processing_duration_ms: float
```

### NetworkSnapshot

```python
class NetworkSnapshot(BaseModel):
    snapshot_id: str
    epoch: int
    timestamp: datetime
    active_nodes: int
    network_density: float
    avg_clustering: float
    network_resilience_score: float
    domain_competition_index: float
    gini_coefficient: float
    herfindahl_index: float
    top_node_concentration: float
```

---

## Configuration

### FederationConfig

```python
class FederationConfig(BaseModel):
    # Protocol
    supported_protocol_versions: List[str] = ["1.0", "1.1"]

    # Trust thresholds
    trust_thresholds: TrustThresholds

    # Node registry
    node_registry: NodeRegistryConfig

    # Signature
    signature: SignatureConfig
```

### NetworkSimulationConfig

```python
class NetworkSimulationConfig(BaseModel):
    num_nodes: int = 10
    topology: NetworkTopology = NetworkTopology.SMALL_WORLD
    num_epochs: int = 50
    claims_per_epoch: int = 20
    adversarial_ratio: float = 0.1
    random_seed: Optional[int] = None
```

---

## CLI Usage

### Run Simulation

```bash
python -m torq_console.layer12.federation.simulator.run_simulation \
    --mode network \
    --nodes 10 \
    --topology small_world \
    --epochs 50 \
    --scenario baseline
```

### Run Validation Suite

```bash
python -m torq_console.layer12.federation.simulator.run_validation_tests
```

### Run Specific Test

```bash
python -m torq_console.layer12.federation.simulator.run_validation_tests \
    --tests baseline \
    --save \
    --output results.json
```

---

## Phase Completion Status

| Phase | Component | Status |
|-------|-----------|--------|
| 1A | Executor Runtime | ✅ COMPLETE |
| 1B | Safeguards Pipeline | ✅ COMPLETE |
| 2A | Predictive Metrics | ✅ COMPLETE |
| 2B | Multi-Node Simulation | ✅ COMPLETE |

---

## Next Steps

After Layer 12 closure, proceed to:

**Layer 13 - Economic Intelligence**
- EconomicEvaluationEngine
- ResourceAllocationEngine
- BudgetAwarePrioritization
- OpportunityCostModel

This will enable TORQ to decide what actions deserve resources.
