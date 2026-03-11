-- ============================================================================
-- Initialize Validation Results Registry
-- Populates validation_results table with all 194 checks
-- ============================================================================

-- Section A: End-to-End Mission Execution (17 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
-- Section A1: Mission Creation
('A', 'A1.1', 'Mission record created', 'Mission record created in database', 'pending'),
('A', 'A1.2', 'Graph created and linked', 'Graph created and linked to mission', 'pending'),
('A', 'A1.3', 'Nodes and edges persisted', 'Nodes and edges persisted correctly', 'pending'),
('A', 'A1.4', 'Workstreams assigned', 'Workstreams assigned to appropriate nodes', 'pending'),
('A', 'A1.5', 'Graph validation passes', 'Graph validation passes (no orphans, no invalid cycles)', 'pending'),
-- Section A2: Mission Start
('A', 'A2.1', 'Initial ready nodes identified', 'Initial ready nodes identified correctly', 'pending'),
('A', 'A2.2', 'Scheduler dispatches valid nodes', 'Scheduler dispatches only valid ready nodes', 'pending'),
('A', 'A2.3', 'Pending nodes remain blocked', 'Pending nodes remain blocked when dependencies unsatisfied', 'pending'),
('A', 'A2.4', 'Mission status changes to running', 'Mission status changes from draft to running', 'pending'),
-- Section A3: Full Mission Completion
('A', 'A3.1', 'All intended nodes execute', 'All intended nodes execute', 'pending'),
('A', 'A3.2', 'Deliverable nodes complete', 'Deliverable nodes complete', 'pending'),
('A', 'A3.3', 'Outputs persist to workspace', 'Outputs persist to workspace', 'pending'),
('A', 'A3.4', 'Mission final status completed', 'Mission final status = completed', 'pending'),
('A', 'A3.5', 'Completion summary generated', 'Completion summary generated', 'pending'),
('A', 'A3.6', 'Mission 1 completed', 'Mission 1: Market Entry Analysis completed', 'pending'),
('A', 'A3.7', 'Mission 2 completed', 'Mission 2: Product Roadmap Planning completed', 'pending'),
('A', 'A3.8', 'Mission 3 completed', 'Mission 3: Technical Risk Evaluation completed', 'pending')
ON CONFLICT DO NOTHING;

-- Section B: Scheduler and Dependency Validation (14 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
-- Section B1: Dependency Enforcement
('B', 'B1.1', 'Dependencies enforced correctly', 'Dependencies are enforced correctly', 'pending'),
('B', 'B1.2', 'No premature node execution', 'No node executes before dependencies complete', 'pending'),
('B', 'B1.3', 'Graph acyclicity maintained', 'Graph acyclicity is maintained', 'pending'),
('B', 'B1.4', 'Orphan detection works', 'Orphan detection works correctly', 'pending'),
-- Section B2: Parallel Execution
('B', 'B2.1', 'Independent nodes run in parallel', 'Independent nodes run in parallel', 'pending'),
('B', 'B2.2', 'Workstreams isolated properly', 'Workstreams are isolated properly', 'pending'),
('B', 'B2.3', 'No cross-workstream interference', 'No cross-workstream interference', 'pending'),
('B', 'B2.4', 'Parallel speedup observed', 'Parallel execution is faster than sequential', 'pending'),
-- Section B3: Decision Gates
('B', 'B3.1', 'Decision gates enforce thresholds', 'Decision gates enforce quality thresholds', 'pending'),
('B', 'B3.2', 'Low-quality outputs blocked', 'Low-quality outputs are blocked', 'pending'),
('B', 'B3.3', 'Replanning triggered on failures', 'Replanning triggered on decision failures', 'pending'),
('B', 'B3.4', 'Alternative paths explored', 'Alternative paths are explored when needed', 'pending'),
('B', 'B3.5', 'No infinite decision loops', 'No infinite decision loops occur', 'pending'),
('B', 'B3.6', 'Decision outcomes recorded', 'Decision outcomes are recorded', 'pending')
ON CONFLICT DO NOTHING;

-- Section C: Context Bus and Events (19 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('C', 'C1.1', 'node.started events', 'node.started events emitted for each node', 'pending'),
('C', 'C1.2', 'node.completed events', 'node.completed events emitted for each completed node', 'pending'),
('C', 'C1.3', 'node.failed events', 'node.failed events emitted for failures', 'pending'),
('C', 'C1.4', 'artifact.produced events', 'artifact.produced events emitted', 'pending'),
('C', 'C1.5', 'evidence.added events', 'evidence.added events emitted', 'pending'),
('C', 'C1.6', 'handoff.created events', 'handoff.created events emitted', 'pending'),
('C', 'C1.7', 'handoff.delivered events', 'handoff.delivered events emitted', 'pending'),
('C', 'C1.8', 'workstream.phase_changed events', 'workstream.phase_changed events emitted', 'pending'),
('C', 'C1.9', 'decision.required events', 'decision.required events emitted', 'pending'),
('C', 'C2.1', 'Events have timestamps', 'All events have valid timestamps', 'pending'),
('C', 'C2.2', 'Events reference nodes', 'Events correctly reference source nodes', 'pending'),
('C', 'C2.3', 'Event data is complete', 'Event data payloads are complete', 'pending'),
('C', 'C3.1', 'No event duplication', 'No duplicate critical events', 'pending'),
('C', 'C3.2', 'Event ordering preserved', 'Events are in correct order', 'pending'),
('C', 'C4.1', 'Context bus subscribes to all', 'Context bus receives all event types', 'pending'),
('C', 'C4.2', 'Event propagation works', 'Events propagate to all subscribers', 'pending'),
('C', 'C5.1', 'Event metadata captured', 'Event metadata (workstream, agent) captured', 'pending'),
('C', 'C5.2', 'Event correlation works', 'Related events can be correlated', 'pending'),
('C', 'C6.1', '20-100 events per mission', 'Expected event volume observed', 'pending')
ON CONFLICT DO NOTHING;

-- Section D: Structured Handoffs (18 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('D', 'D1.1', 'Handoffs created on node complete', 'Handoffs created when nodes complete', 'pending'),
('D', 'D1.2', 'Handoffs reference source node', 'Handoffs correctly reference from_node_id', 'pending'),
('D', 'D1.3', 'Handoffs specify target agent', 'Handoffs specify to_agent_type', 'pending'),
('D', 'D2.1', 'Handoff summary present', 'handoff_summary field populated', 'pending'),
('D', 'D2.2', 'Summary has objective_completed', 'Summary includes objective_completed', 'pending'),
('D', 'D2.3', 'Summary has output_summary', 'Summary includes output_summary', 'pending'),
('D', 'D3.1', 'Confidence score present', 'Confidence score in valid range', 'pending'),
('D', 'D3.2', 'Confidence basis provided', 'Confidence basis explained', 'pending'),
('D', 'D4.1', 'Unresolved questions listed', 'Unresolved questions array populated', 'pending'),
('D', 'D4.2', 'Assumptions documented', 'Assumptions made are documented', 'pending'),
('D', 'D4.3', 'Limitations documented', 'Limitations are documented', 'pending'),
('D', 'D5.1', 'Risks flagged', 'Risks array populated', 'pending'),
('D', 'D5.2', 'Severity indicators present', 'Severity indicators provided', 'pending'),
('D', 'D6.1', 'Artifacts attached', 'Artifacts JSONB populated', 'pending'),
('D', 'D6.2', 'Workspace entries linked', 'Workspace entries referenced', 'pending'),
('D', 'D7.1', '5-20 handoffs per mission', 'Expected handoff volume observed', 'pending'),
('D', 'D8.1', 'Handoff delivery tracked', 'Handoff status tracked through delivery', 'pending'),
('D', 'D8.2', 'Handoff acknowledgments captured', 'Acknowledging agents recorded', 'pending')
ON CONFLICT DO NOTHING;

-- Section E: Workstream State Tracking (13 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('E', 'E1.1', 'Workstreams created', 'Workstream states created for mission', 'pending'),
('E', 'E1.2', 'Workstreams linked to mission', 'Workstreams reference mission_id', 'pending'),
('E', 'E2.1', 'Phase progression works', 'Phases progress sequentially', 'pending'),
('E', 'E2.2', 'All phases visited', 'All expected phases visited', 'pending'),
('E', 'E3.1', 'Health state tracked', 'Health state (healthy/at_risk/critical) tracked', 'pending'),
('E', 'E3.2', 'Health changes captured', 'Health state changes logged', 'pending'),
('E', 'E4.1', 'Progress percent accurate', 'Progress percent reflects completion', 'pending'),
('E', 'E4.2', 'Node counts accurate', 'Total/completed/failed nodes accurate', 'pending'),
('E', 'E5.1', 'Blockers documented', 'Blockers JSONB populated', 'pending'),
('E', 'E5.2', 'Open questions tracked', 'Open questions array maintained', 'pending'),
('E', 'E6.1', 'Workstream dependencies tracked', 'depends_on_workstreams array correct', 'pending'),
('E', 'E6.2', 'Dependency waiting works', 'waiting_for_dependencies flag works', 'pending'),
('E', 'E7.1', '2-4 workstreams per mission', 'Expected workstream count observed', 'pending')
ON CONFLICT DO NOTHING;

-- Section F: Replanning Engine (15 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('F', 'F1.1', 'Replanning triggers on failure', 'Replanning triggered when nodes fail', 'pending'),
('F', 'F1.2', 'Replanning triggers on timeout', 'Replanning triggered when nodes timeout', 'pending'),
('F', 'F2.1', 'New nodes created', 'Replanning creates new nodes', 'pending'),
('F', 'F2.2', 'New edges created', 'Replanning creates new edges', 'pending'),
('F', 'F2.3', 'Invalid nodes marked', 'Invalid nodes marked for skip', 'pending'),
('F', 'F3.1', 'Graph version updated', 'Graph version incremented on replan', 'pending'),
('F', 'F3.2', 'Old graph preserved', 'Previous graph state preserved', 'pending'),
('F', 'F4.1', 'Replan reason captured', 'Reason for replan documented', 'pending'),
('F', 'F4.2', 'Replan strategy recorded', 'Strategy used recorded', 'pending'),
('F', 'F5.1', 'No infinite replan loops', 'Replanning has max iteration limit', 'pending'),
('F', 'F5.2', 'Replan convergence', 'Replanning converges to solution', 'pending'),
('F', 'F6.1', 'Affected nodes notified', 'Affected nodes notified of replan', 'pending'),
('F', 'F6.2', 'Downstream updates work', 'Downstream dependencies updated', 'pending'),
('F', 'F7.1', 'Replan telemetry captured', 'Replan metrics captured', 'pending'),
('F', 'F7.2', 'Replan quality tracked', 'Replan quality assessment tracked', 'pending')
ON CONFLICT DO NOTHING;

-- Section G: Checkpoint and Recovery (16 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('G', 'G1.1', 'Checkpoints created', 'Checkpoints created at intervals', 'pending'),
('G', 'G1.2', '3-10 checkpoints per mission', 'Expected checkpoint volume observed', 'pending'),
('G', 'G2.1', 'Node states captured', 'Node states captured in checkpoints', 'pending'),
('G', 'G2.2', 'Partial outputs captured', 'Partial outputs preserved', 'pending'),
('G', 'G3.1', 'Checkpoint can restore', 'Checkpoint can restore node states', 'pending'),
('G', 'G3.2', 'Restore recovers outputs', 'Restore recovers completed outputs', 'pending'),
('G', 'G4.1', 'Rollback to checkpoint', 'Can rollback to checkpoint', 'pending'),
('G', 'G4.2', 'Rollback resets states', 'Rollback resets node states', 'pending'),
('G', 'G5.1', 'Resume after checkpoint', 'Execution resumes after restore', 'pending'),
('G', 'G5.2', 'Resume maintains context', 'Context maintained across resume', 'pending'),
('G', 'G6.1', 'Checkpoint pruning works', 'Old checkpoints pruned', 'pending'),
('G', 'G6.2', 'Max checkpoints enforced', 'Max checkpoint limit enforced', 'pending'),
('G', 'G7.1', 'Checkpoint metadata captured', 'Checkpoint metadata preserved', 'pending'),
('G', 'G7.2', 'Checkpoint size managed', 'Checkpoint storage is reasonable', 'pending'),
('G', 'G8.1', 'Recovery under interruption', 'Mission can recover from interruption', 'pending'),
('G', 'G8.2', 'No data loss on recovery', 'No data loss after recovery', 'pending')
ON CONFLICT DO NOTHING;

-- Section H: Integration Integrity (15 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('H', 'H1.1', 'Workspace integration works', 'Outputs persist to workspace', 'pending'),
('H', 'H1.2', 'Workspace entries referenced', 'Handoffs reference workspace entries', 'pending'),
('H', 'H2.1', 'Synthesis integration works', 'Multiple outputs synthesized', 'pending'),
('H', 'H2.2', 'Synthesis outputs captured', 'Synthesis results stored', 'pending'),
('H', 'H3.1', 'Evaluation integration works', 'Outputs evaluated', 'pending'),
('H', 'H3.2', 'Evaluation scores captured', 'Evaluation metrics stored', 'pending'),
('H', 'H4.1', 'Strategic memory injection', 'Memories injected at start', 'pending'),
('H', 'H4.2', 'Memory effectiveness tracked', 'Memory effectiveness measured', 'pending'),
('H', 'H5.1', 'No circular dependencies', 'No circular dependencies across systems', 'pending'),
('H', 'H5.2', 'Data flow consistent', 'Data flows correctly across subsystems', 'pending'),
('H', 'H6.1', 'Cross-system references work', 'Cross-references (handoffs->workspace) work', 'pending'),
('H', 'H6.2', 'ID references are valid', 'All ID references point to valid records', 'pending'),
('H', 'H7.1', 'Transaction boundaries work', 'Multi-step operations use transactions', 'pending'),
('H', 'H7.2', 'Rollback works on failure', 'Failed operations roll back correctly', 'pending'),
('H', 'H8.1', 'End-to-end integration passes', 'Full integration test passes', 'pending')
ON CONFLICT DO NOTHING;

-- Section I: Observability and Traceability (12 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('I', 'I1.1', 'Full mission trace available', 'Can trace full mission execution', 'pending'),
('I', 'I1.2', 'Node execution traceable', 'Can trace individual node execution', 'pending'),
('I', 'I2.1', 'Events queryable', 'Events can be queried by filters', 'pending'),
('I', 'I2.2', 'Handoffs queryable', 'Handoffs can be queried', 'pending'),
('I', 'I3.1', 'Telemetry captured', 'Runtime telemetry captured', 'pending'),
('I', 'I3.2', 'Metrics are accurate', 'Telemetry metrics are accurate', 'pending'),
('I', 'I4.1', 'Debug information available', 'Debug info accessible', 'pending'),
('I', 'I4.2', 'Logs are structured', 'Logs are structured and parseable', 'pending'),
('I', 'I5.1', 'Performance metrics available', 'Performance metrics captured', 'pending'),
('I', 'I5.2', 'Resource usage tracked', 'Resource usage (tokens, time) tracked', 'pending'),
('I', 'I6.1', 'Audit trail complete', 'Complete audit trail available', 'pending'),
('I', 'I6.2', 'Timeline reconstructable', 'Execution timeline can be reconstructed', 'pending')
ON CONFLICT DO NOTHING;

-- Section J: Performance and Stability (11 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('J', 'J1.1', 'Concurrent execution works', 'Concurrent node execution works', 'pending'),
('J', 'J1.2', 'No race conditions', 'No race conditions observed', 'pending'),
('J', 'J2.1', 'Execution time reasonable', 'Mission completes in reasonable time', 'pending'),
('J', 'J2.2', 'No memory leaks', 'No memory leaks detected', 'pending'),
('J', 'J3.1', 'Event overhead acceptable', 'Event system overhead is acceptable', 'pending'),
('J', 'J3.2', 'Handoff overhead acceptable', 'Handoff overhead is acceptable', 'pending'),
('J', 'J3.3', 'Checkpoint overhead acceptable', 'Checkpoint overhead is acceptable', 'pending'),
('J', 'J4.1', 'Handles large graphs', 'Can handle large (20+ node) graphs', 'pending'),
('J', 'J4.2', 'Handles deep graphs', 'Can handle deep (10+ layers) graphs', 'pending'),
('J', 'J5.1', 'Error recovery works', 'System recovers from errors', 'pending'),
('J', 'J5.2', 'Graceful degradation', 'System degrades gracefully under load', 'pending')
ON CONFLICT DO NOTHING;

-- Section K: Subsystem Maturity Classification (6 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('K', 'K1', 'Context Bus classification', 'Context Bus maturity classified', 'pending'),
('K', 'K2', 'Structured Handoffs classification', 'Structured Handoffs maturity classified', 'pending'),
('K', 'K3', 'Workstream State Tracking classification', 'Workstream State Tracking maturity classified', 'pending'),
('K', 'K4', 'Replanning Engine classification', 'Replanning Engine maturity classified', 'pending'),
('K', 'K5', 'Checkpoint/Recovery classification', 'Checkpoint/Recovery maturity classified', 'pending'),
('K', 'K6', 'Mission Graph Scheduling classification', 'Mission Graph Scheduling maturity classified', 'pending')
ON CONFLICT DO NOTHING;

-- Section N: Output Quality Validation (9 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('N', 'N1.1', 'Mission Graph executed', 'Mission Graph mode executed successfully', 'pending'),
('N', 'N1.2', 'Single Agent executed', 'Single Agent mode executed successfully', 'pending'),
('N', 'N2.1', 'Evaluation score MG >= SA', 'Mission Graph evaluation score >= Single Agent', 'pending'),
('N', 'N2.2', 'Reasoning coherence MG >= SA', 'Reasoning coherence Mission Graph >= Single Agent', 'pending'),
('N', 'N2.3', 'Contradiction rate MG < SA', 'Contradiction rate Mission Graph < Single Agent', 'pending'),
('N', 'N2.4', 'Deliverable completeness MG >= SA', 'Deliverable completeness Mission Graph >= Single Agent', 'pending'),
('N', 'N2.5', 'Execution time reasonable', 'Mission Graph execution time within 2x of Single Agent', 'pending'),
('N', 'N2.6', 'Token usage efficient', 'Token usage is efficient', 'pending'),
('N', 'N3.1', 'Architecture improvements demonstrated', 'At least 3 architectural improvements clearly demonstrated', 'pending')
ON CONFLICT DO NOTHING;

-- Section O: Runtime Telemetry Capture (13 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('O', 'O1.1', 'Telemetry schema created', 'validation_telemetry table exists', 'pending'),
('O', 'O2.1', 'Mission 1 telemetry captured', 'Mission 1 telemetry captured', 'pending'),
('O', 'O2.2', 'Mission 2 telemetry captured', 'Mission 2 telemetry captured', 'pending'),
('O', 'O2.3', 'Mission 3 telemetry captured', 'Mission 3 telemetry captured', 'pending'),
('O', 'O2.4', 'All required metrics captured', 'All required telemetry metrics captured', 'pending'),
('O', 'O3.1', 'Aggregate metrics computable', 'Can compute aggregate metrics', 'pending'),
('O', 'O3.2', 'Average duration calculable', 'Average mission duration calculated', 'pending'),
('O', 'O3.3', 'Average nodes calculable', 'Average node count calculated', 'pending'),
('O', 'O3.4', 'Average handoffs calculable', 'Average handoff count calculated', 'pending'),
('O', 'O3.5', 'Average score calculable', 'Average evaluation score calculated', 'pending'),
('O', 'O4.1', 'Telemetry queryable', 'Telemetry can be queried by mission type', 'pending'),
('O', 'O4.2', 'Telemetry exportable', 'Telemetry can be exported for reporting', 'pending'),
('O', 'O4.3', 'Telemetry documented', 'Telemetry metrics documented in README', 'pending')
ON CONFLICT DO NOTHING;

-- Section P: Memory Injection Sanity Check (13 checks)
INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
('P', 'P1.1', 'Average memories <= 5', 'Average memories injected per node <= 5', 'pending'),
('P', 'P1.2', 'Max memories <= 10', 'No node receives >10 memories', 'pending'),
('P', 'P2.1', 'Injection success rate >= 80%', 'Memory injection success rate >= 80%', 'pending'),
('P', 'P2.2', 'Memory relevance adequate', 'Injected memories are relevant', 'pending'),
('P', 'P3.1', 'Conflict rate <= 10%', 'Memory conflict rate <= 10%', 'pending'),
('P', 'P3.2', 'Conflicts resolved', 'Memory conflicts are resolved', 'pending'),
('P', 'P4.1', 'No context flooding', 'Prompt size <= 80% of context window', 'pending'),
('P', 'P4.2', 'Memory size reasonable', 'Memory size is reasonable', 'pending'),
('P', 'P5.1', 'Attribution score tracked', 'Memory attribution score tracked', 'pending'),
('P', 'P5.2', 'Attribution accurate', 'Memory attribution is accurate', 'pending'),
('P', 'P6.1', 'Scope enforcement works', 'Memory scope enforcement works', 'pending'),
('P', 'P6.2', 'Global vs scoped memories', 'Global and scoped memories handled correctly', 'pending'),
('P', 'P7.1', 'Memory sanity validation passes', 'Overall memory sanity check passes', 'pending')
ON CONFLICT DO NOTHING;

-- Verify initialization
SELECT section, COUNT(*) as check_count
FROM validation_results
GROUP BY section
ORDER BY section;
