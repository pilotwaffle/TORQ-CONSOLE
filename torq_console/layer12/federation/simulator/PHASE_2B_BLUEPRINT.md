# Layer 12 Phase 2B Implementation Blueprint

**Status:** READY TO BEGIN
**Start Date:** March 14, 2026
**Baseline:** v0.12.2a (Phase 2A complete)

---

## Overview

Phase 2B transforms the 2-node simulator into a **multi-node federation network simulation** capable of modeling 10-50 nodes with realistic topology, event-driven behavior, and network-scale collapse detection.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Phase 2B Network Architecture                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │ EventScheduler  │───▶│ NetworkController│───▶│  NodeRegistry   │         │
│  │                 │    │                 │    │                 │         │
│  │ - Event queue   │    │ - Topology mgmt │    │ - Node identity │         │
│  │ - Time advance  │    │ - Epoch orchest │    │ - Trust state   │         │
│  │ - Trigger exec  │    │ - Routing       │    │ - Domain spec   │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│           │                      │                      │                   │
│           ▼                      ▼                      ▼                   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │ NetworkMetrics  │    │ ProcessorAdapter│    │ Phase 2A Core   │         │
│  │                 │    │ (from Phase 2A) │    │                 │         │
│  │ - Centrality   │    │ - Claim process │    │ - Safeguards    │         │
│  │ - Clustering   │    │ - Result normal │    │ - Predictive    │         │
│  │ - Path length  │    │                 │    │ - Health index  │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
torq_console/layer12/federation/simulator/
├── phase2b/
│   ├── __init__.py                    # Phase 2B package exports
│   ├── node_registry.py               # ✨ NEW: Node identity and state management
│   ├── network_controller.py          # ✨ NEW: Topology and orchestration
│   ├── event_scheduler.py             # ✨ NEW: Event-driven simulation engine
│   ├── network_metrics.py             # ✨ NEW: Network-scale metrics
│   ├── topologies.py                  # ✨ NEW: Topology generators
│   ├── behaviors.py                   # ✨ NEW: Node behavior profiles
│   └── executor_network.py            # ✨ NEW: Network simulation executor
├── models.py                          # Extended with network models
├── scenarios.py                       # Extended with Phase 2B scenarios
└── run_network_simulation.py          # ✨ NEW: CLI for network simulations
```

---

## Implementation Order

### Step 1: NodeRegistry (Commit 1)

**File:** `phase2b/node_registry.py`

**Purpose:** Centralized node identity, state, and behavior management.

**Key Models:**

```python
@dataclass
class NodeIdentity:
    """Unique node identity and credentials."""
    node_id: str
    display_name: str
    public_key: str
    key_id: str
    created_at: datetime

@dataclass
class NodeTrustState:
    """Dynamic trust state for a node."""
    node_id: str
    baseline_trust: float = 0.5
    current_trust: float = 0.5
    trust_velocity: float = 0.0  # Rate of change
    quarantined: bool = False
    quarantine_reason: Optional[str] = None
    adjustment_history: List[float] = field(default_factory=list)

@dataclass
class DomainSpecialization:
    """Node's domain expertise and influence."""
    primary_domain: Domain
    secondary_domains: List[Domain]
    domain_confidence: Dict[Domain, float]  # domain -> confidence score
    publication_count: Dict[Domain, int]    # domain -> claim count

@dataclass
class InfluenceProfile:
    """Node's influence in the federation."""
    node_id: str
    raw_influence: float = 0.0
    normalized_influence: float = 0.0
    domain_dominance: Dict[Domain, float] = field(default_factory=dict)
    follower_count: int = 0
    citation_count: int = 0

@dataclass
class BehaviorProfile:
    """Node's behavioral tendencies."""
    node_id: str
    claim_frequency: float = 1.0  # claims per epoch
    stance_distribution: Dict[Stance, float] = field(default_factory=dict)
    quality_mean: float = 0.7
    quality_std: float = 0.15
    adversarial_mode: Optional[str] = None  # None, "flood", "monoculture", "capture"
    adversarial_intensity: float = 0.0

@dataclass
class FederatedNode:
    """Complete node representation for Phase 2B."""
    identity: NodeIdentity
    trust_state: NodeTrustState
    domain_spec: DomainSpecialization
    influence: InfluenceProfile
    behavior: BehaviorProfile
    connections: Set[str] = field(default_factory=set)  # Connected node IDs
```

**Key Methods:**

```python
class NodeRegistry:
    """Registry for all nodes in the federation simulation."""

    def __init__(self):
        self.nodes: Dict[str, FederatedNode] = {}
        self.identity_index: Dict[str, NodeIdentity] = {}
        self.trust_index: Dict[str, NodeTrustState] = {}

    def register_node(self, node: FederatedNode) -> None:
        """Register a new node in the federation."""

    def get_node(self, node_id: str) -> Optional[FederatedNode]:
        """Get a node by ID."""

    def update_trust(self, node_id: str, adjustment: float) -> None:
        """Update trust score and track velocity."""

    def get_influential_nodes(self, top_n: int = 5) -> List[FederatedNode]:
        """Get top N nodes by influence."""

    def get_nodes_by_domain(self, domain: Domain) -> List[FederatedNode]:
        """Get nodes specializing in a domain."""

    def apply_trust_decay(self, decay_rate: float = 0.01) -> None:
        """Apply trust decay to all nodes."""
```

---

### Step 2: NetworkController (Commit 2)

**File:** `phase2b/network_controller.py`

**Purpose:** Topology creation, node spawning, epoch orchestration, and message routing.

**Key Models:**

```python
@dataclass
class NetworkTopology:
    """Represents the federation network structure."""
    topology_id: str
    topology_type: str  # "small_world", "scale_free", "random", "hierarchical"
    node_count: int
    edge_count: int
    adjacency_list: Dict[str, Set[str]]  # node_id -> neighbors
    connection_matrix: Optional[np.ndarray] = None

    def average_degree(self) -> float:
        """Average node degree."""

    def clustering_coefficient(self) -> float:
        """Network clustering coefficient."""

    def average_path_length(self) -> float:
        """Average shortest path length."""

@dataclass
class NetworkConfig:
    """Configuration for network generation."""
    node_count: int = 10
    topology_type: str = "small_world"
    connection_probability: float = 0.3  # For random graphs
    rewiring_probability: float = 0.1   # For small-world
    attachment_exponent: float = 2.0     # For scale-free
    min_connections: int = 2
    max_connections: int = 5

@dataclass
class EpochConfig:
    """Configuration for simulation epochs."""
    epochs: int = 20
    claims_per_epoch: int = 50
    event_interval_ms: int = 100
    enable_adversarial_events: bool = True
    adversarial_probability: float = 0.1
```

**Key Methods:**

```python
class NetworkController:
    """Controls network topology and orchestration."""

    def __init__(self, registry: NodeRegistry, config: NetworkConfig):
        self.registry = registry
        self.config = config
        self.topology: Optional[NetworkTopology] = None

    def build_topology(self) -> NetworkTopology:
        """Build the network topology based on config."""

    def spawn_nodes(self, count: int, behavior_profile: str = "mixed") -> List[str]:
        """Spawn new nodes with specified behavior profile."""

    def route_claim(self, claim: FederatedClaimEnvelope, source: str, target: str) -> bool:
        """Route a claim from source to target."""

    def broadcast_claim(self, claim: FederatedClaimEnvelope, source: str, radius: int = 1):
        """Broadcast claim to neighbors within radius."""

    def get_network_snapshot(self) -> Dict[str, Any]:
        """Get current network state snapshot."""
```

---

### Step 3: EventScheduler (Commit 3)

**File:** `phase2b/event_scheduler.py`

**Purpose:** Event-driven simulation engine replacing loop-based execution.

**Key Models:**

```python
@dataclass
class SimulationEvent:
    """Base class for simulation events."""
    event_id: str
    timestamp: float
    event_type: str
    priority: int = 0

    def __lt__(self, other):
        """For priority queue ordering."""

@dataclass
class ClaimPublicationEvent(SimulationEvent):
    """Event: Node publishes a claim."""
    node_id: str
    claim: SimulatedClaim
    target_nodes: List[str]

@dataclass
class TrustAdjustmentEvent(SimulationEvent):
    """Event: Trust score adjustment."""
    node_id: str
    adjustment: float
    reason: str

@dataclass
class NodeJoinEvent(SimulationEvent):
    """Event: New node joins federation."""
    node: FederatedNode

@dataclass
class NodeLeaveEvent(SimulationEvent):
    """Event: Node leaves federation."""
    node_id: str
    reason: str

@dataclass
class EpochEndEvent(SimulationEvent):
    """Event: Epoch boundary marker."""
    epoch_number: int
    epoch_metrics: Dict[str, Any]
```

**Key Methods:**

```python
class EventScheduler:
    """Event-driven simulation scheduler."""

    def __init__(self, controller: NetworkController):
        self.controller = controller
        self.event_queue: PriorityQueue[SimulationEvent] = PriorityQueue()
        self.current_time: float = 0.0
        self.event_log: List[SimulationEvent] = []

    def schedule(self, event: SimulationEvent) -> None:
        """Schedule an event for execution."""

    def schedule_claim_publication(self, node_id: str, delay: float = 0.0) -> None:
        """Schedule a claim publication from a node."""

    def schedule_epoch_end(self, epoch_number: int, timestamp: float) -> None:
        """Schedule epoch boundary."""

    def run(self, duration: float) -> None:
        """Run simulation until time duration."""

    def step(self) -> bool:
        """Execute next event. Returns False if no events remain."""

    async def process_event(self, event: SimulationEvent) -> None:
        """Process a single event."""
```

---

### Step 4: NetworkMetrics (Commit 4)

**File:** `phase2b/network_metrics.py`

**Purpose:** Network-scale metrics for observing failure patterns.

**Key Models:**

```python
@dataclass
class CentralityMetrics:
    """Centrality measures for network analysis."""
    degree_centrality: Dict[str, float]      # Node connection importance
    betweenness_centrality: Dict[str, float]  # Node bridge importance
    eigenvector_centrality: Dict[str, float]  # Node influence importance
    pagerank: Dict[str, float]                # PageRank scores

@dataclass
class NetworkHealthMetrics:
    """Network-level health indicators."""
    density: float                           # Connection density
    clustering: float                        # Clustering coefficient
    avg_path_length: float                   # Average shortest path
    diameter: int                            # Longest shortest path
    connected_components: int                # Network fragmentation

@dataclass
class InfluenceDistribution:
    """Inequality metrics for influence distribution."""
    gini_coefficient: float                  # 0 = equal, 1 = maximal inequality
    herfindahl_index: float                  # Market concentration
    top_1_share: float                       # Top node's share
    top_5_share: float                       # Top 5 nodes' share
    lorenz_curve: List[Tuple[float, float]]  # Cumulative share

@dataclass
class NetworkCollapseIndicators:
    """Leading indicators of network collapse."""
    fragmentation_acceleration: float        # Rate of component splitting
    centrality_concentration: float          # Power centralizing in few nodes
    bridge_failure_rate: float               # Critical edges failing
    information_bottleneck_score: float      # Flow concentration
    cascade_risk: float                      # Cascading failure probability
```

**Key Methods:**

```python
class NetworkMetricsCalculator:
    """Calculate network-scale metrics."""

    def __init__(self, controller: NetworkController):
        self.controller = controller

    def calculate_centrality(self) -> CentralityMetrics:
        """Calculate all centrality measures."""

    def calculate_network_health(self) -> NetworkHealthMetrics:
        """Calculate network health indicators."""

    def calculate_influence_distribution(self) -> InfluenceDistribution:
        """Calculate influence inequality metrics."""

    def calculate_collapse_indicators(self) -> NetworkCollapseIndicators:
        """Calculate collapse risk indicators."""

    def detect_critical_nodes(self, threshold: float = 0.8) -> List[str]:
        """Detect nodes whose removal would fragment the network."""
```

---

## Scenario Progression

### Scenario 1: Baseline Small-World (10 nodes)

**Purpose:** Validate basic network functionality.

**Configuration:**
- 10 nodes
- Small-world topology (Watts-Strogatz)
- 20 epochs
- 50 claims/epoch
- No adversarial behavior

**Success Criteria:**
- All nodes participate
- Claims route correctly
- Metrics compute successfully
- No network fragmentation

### Scenario 2: Authority Accretion (10 nodes)

**Purpose:** Test influence damping and plurality preservation.

**Configuration:**
- 10 nodes, 2 dominant
- Gradual authority bias
- 30 epochs
- 60 claims/epoch

**Success Criteria:**
- ACA detects concentration early
- Plurality flags trigger
- Minority viewpoints preserved
- FCRI stays healthy

### Scenario 3: Domain Competition (20 nodes)

**Purpose:** Test domain-specific influence dynamics.

**Configuration:**
- 20 nodes across 5 domains
- Domain echo chambers
- 30 epochs

**Success Criteria:**
- Cross-domain claims accepted
- Domain diversity preserved
- No monoculture formation

### Scenario 4: Sybil Attack (15 nodes, 5 Sybil)

**Purpose:** Test identity spoofing detection.

**Configuration:**
- 10 genuine nodes
- 5 Sybil nodes with coordinated behavior
- 25 epochs

**Success Criteria:**
- Sybil nodes detected
- Trust decays for Sybil cluster
- Genuine nodes unaffected

### Scenario 5: Network Partition Recovery (20 nodes)

**Purpose:** Test resilience to network splits.

**Configuration:**
- 20 nodes
- Simulated partition at epoch 15
- Reconnection at epoch 20
- 30 epochs total

**Success Criteria:**
- Partition detected
- Claims queued during partition
- Recovery successful
- No data loss

### Scenario 6: Scale-Free Stress Test (50 nodes)

**Purpose:** Validate scaling to larger networks.

**Configuration:**
- 50 nodes
- Scale-free topology (Barabási-Albert)
- 40 epochs
- 100 claims/epoch

**Success Criteria:**
- Performance remains acceptable
- Predictive metrics compute correctly
- No cascade failures

---

## CLI Interface

```bash
# Run baseline small-world scenario
python -m torq_console.layer12.federation.simulator.run_network_simulation \
    --scenario baseline_small_world \
    --nodes 10 \
    --epochs 20

# Run authority accretion scenario
python -m torq_console.layer12.federation.simulator.run_network_simulation \
    --scenario authority_accretion \
    --nodes 10 \
    --epochs 30 \
    --dominant-nodes 2

# Run scale-free stress test
python -m torq_console.layer12.federation.simulator.run_network_simulation \
    --scenario scale_free_stress \
    --nodes 50 \
    --epochs 40 \
    --topology scale_free

# List available scenarios
python -m torq_console.layer12.federation.simulator.run_network_simulation \
    --list

# Visualize network topology
python -m torq_console.layer12.federation.simulator.run_network_simulation \
    --scenario baseline_small_world \
    --visualize
```

---

## Commit Sequence

1. `Add NodeRegistry for multi-node federation simulation`
   - node_registry.py with all node models
   - Basic registration and lookup

2. `Add NetworkController for topology and epoch orchestration`
   - network_controller.py with topology builders
   - Routing and broadcast methods
   - Small-world and scale-free generators

3. `Add event-driven scheduler for federation network simulation`
   - event_scheduler.py with event types
   - Priority queue execution
   - Epoch boundary handling

4. `Add network-scale metrics for multi-node federation analysis`
   - network_metrics.py with centrality calculators
   - Collapse indicators
   - Influence distribution metrics

5. `Add network simulation executor with Phase 2B scenarios`
   - executor_network.py
   - 6 Phase 2B scenarios
   - CLI runner

6. `Layer 12 Phase 2B Complete — Multi-Node Federation Scale Validation`
   - Final tag: v0.12.2b

---

## Dependencies

```txt
# Existing (from Phase 2A)
- pydantic
- asyncio
- hashlib
- datetime
- typing

# New for Phase 2B
- numpy  # For matrix operations and centrality calculations
- networkx  # For topology generation and graph algorithms (optional, can implement ourselves)
- heapq  # For priority queue (built-in)
- collections  # For deque, defaultdict (built-in)
```

---

## Success Criteria

Phase 2B is complete when:

1. ✅ NodeRegistry manages 50+ nodes
2. ✅ NetworkController generates multiple topologies
3. ✅ EventScheduler runs event-driven simulations
4. ✅ NetworkMetrics calculate all centrality measures
5. ✅ All 6 scenarios execute successfully
6. ✅ Predictive metrics (EDDR, ACA, FCRI) work at network scale
7. ✅ CLI supports scenario selection and visualization
8. ✅ Performance acceptable for 50-node networks

---

**Phase 2B implementation can now begin.**
