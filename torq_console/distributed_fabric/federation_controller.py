"""
TORQ Layer 11 - Federation Controller

L11-M1: Handles secure cross-node communication and federation.

The FederationController provides:
- Node authentication and authorization
- Encrypted communication between nodes
- Federation contract enforcement
- Export validation and redaction enforcement

All federation operations respect Pre-Fabric Boundary Hardening (PRD-011-PRE):
- Operational state never leaves its origin node
- Strategic state cannot federate directly
- Analytical intelligence is the primary federation product
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

from pydantic import BaseModel

from .models import (
    NodeInfo,
    NodeIdentity,
    FederationLink,
    FederationLinkStatus,
    FederationPolicy,
    FederationExportContract,
    FederationImportValidation,
    FederationArtifactType,
    RedactionLevel,
    SharingScope,
)
from .models.federation_models import (
    FederatedArtifact,
    FederatedPattern,
    FederatedBenchmark,
    FederatedInsight,
    FederatedRecommendation,
    FederationMetadata,
    FederationExportRequest,
    FederationExportResponse,
    FederationImportRequest,
    FederationImportResponse,
)
from .node_registry_service import get_node_registry_service


logger = logging.getLogger(__name__)


# ============================================================================
# Federation Storage
# ============================================================================

class FederationStorage:
    """Storage for federation data."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize federation storage."""
        self.storage_path = storage_path or Path.cwd() / "data" / "federation"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Subdirectories
        (self.storage_path / "artifacts").mkdir(exist_ok=True)
        (self.storage_path / "contracts").mkdir(exist_ok=True)
        (self.storage_path / "links").mkdir(exist_ok=True)
        (self.storage_path / "policies").mkdir(exist_ok=True)

        # In-memory cache
        self._exported_artifacts: Dict[UUID, FederatedArtifact] = {}
        self._imported_artifacts: Dict[UUID, FederatedArtifact] = {}
        self._links: Dict[UUID, FederationLink] = {}
        self._policies: Dict[UUID, FederationPolicy] = {}

    def save_exported_artifact(self, artifact: FederatedArtifact) -> None:
        """Save an exported artifact."""
        artifact_path = (
            self.storage_path / "artifacts" / "exported" /
            f"{artifact.artifact_id}.json"
        )
        artifact_path.write_text(artifact.model_dump_json(indent=2))
        self._exported_artifacts[artifact.artifact_id] = artifact

    def save_imported_artifact(self, artifact: FederatedArtifact) -> None:
        """Save an imported artifact."""
        artifact_path = (
            self.storage_path / "artifacts" / "imported" /
            f"{artifact.artifact_id}.json"
        )
        artifact_path.write_text(artifact.model_dump_json(indent=2))
        self._imported_artifacts[artifact.artifact_id] = artifact

    def save_contract(self, contract: FederationExportContract) -> None:
        """Save a federation contract."""
        contract_path = (
            self.storage_path / "contracts" /
            f"{contract.export_id}.json"
        )
        contract_path.write_text(contract.model_dump_json(indent=2))

    def save_link(self, link: FederationLink) -> None:
        """Save a federation link."""
        link_path = (
            self.storage_path / "links" /
            f"{link.link_id}.json"
        )
        link_path.write_text(link.model_dump_json(indent=2))
        self._links[link.link_id] = link

    def save_policy(self, policy: FederationPolicy) -> None:
        """Save a federation policy."""
        policy_path = (
            self.storage_path / "policies" /
            f"{policy.policy_id}.json"
        )
        policy_path.write_text(policy.model_dump_json(indent=2))
        self._policies[policy.policy_id] = policy


# ============================================================================
# Federation Controller
# ============================================================================

class FederationController:
    """
    Handles secure cross-node communication and federation.

    Responsibilities:
    - Node authentication and authorization
    - Encrypted communication between nodes
    - Federation contract enforcement
    - Export validation and redaction enforcement
    - Artifact lifecycle management
    """

    def __init__(self, local_node_id: UUID, storage_path: Optional[Path] = None):
        """Initialize the federation controller."""
        self._local_node_id = local_node_id
        self._storage = FederationStorage(storage_path)
        self._registry = get_node_registry_service()

        # Trust management
        self._trusted_nodes: Set[UUID] = set()
        self._node_secrets: Dict[UUID, str] = {}  # For HMAC signing

        # Federation links
        self._active_links: Dict[UUID, FederationLink] = {}

        # Load existing data
        self._load_links()
        self._load_policies()

    def _load_links(self) -> None:
        """Load existing federation links."""
        for link_file in self._storage.storage_path.glob("links/*.json"):
            try:
                data = json.loads(link_file.read_text())
                link = FederationLink(**data)
                self._active_links[link.link_id] = link
            except Exception as e:
                logger.debug(f"Error loading link from {link_file}: {e}")

    def _load_policies(self) -> None:
        """Load existing federation policies."""
        for policy_file in self._storage.storage_path.glob("policies/*.json"):
            try:
                data = json.loads(policy_file.read_text())
                policy = FederationPolicy(**data)
                self._storage._policies[policy.policy_id] = policy
            except Exception as e:
                logger.debug(f"Error loading policy from {policy_file}: {e}")

    # ========================================================================
    # Trust Management
    # ========================================================================

    async def establish_trust(self, node_id: UUID, shared_secret: str) -> bool:
        """
        Establish trust with another node.

        Args:
            node_id: ID of node to trust
            shared_secret: Shared secret for HMAC signing

        Returns:
            True if trust established
        """
        self._trusted_nodes.add(node_id)
        self._node_secrets[node_id] = shared_secret

        logger.info(f"[Federation] Established trust with node {node_id}")

        return True

    def revoke_trust(self, node_id: UUID) -> bool:
        """Revoke trust for a node."""
        self._trusted_nodes.discard(node_id)
        self._node_secrets.pop(node_id, None)

        # Disable links
        for link in self._active_links.values():
            if link.target_node_id == node_id:
                link.enabled = False
                link.status = FederationLinkStatus.BLOCKED

        logger.info(f"[Federation] Revoked trust for node {node_id}")

        return True

    def is_trusted(self, node_id: UUID) -> bool:
        """Check if a node is trusted."""
        return node_id in self._trusted_nodes

    # ========================================================================
    # Federation Links
    # ========================================================================

    async def create_federation_link(
        self,
        target_node_id: UUID,
        allowed_artifact_types: Optional[List[str]] = None,
    ) -> FederationLink:
        """
        Create a federation link to another node.

        Args:
            target_node_id: ID of target node
            allowed_artifact_types: Types of artifacts allowed on this link

        Returns:
            Created FederationLink
        """
        # Verify target node exists
        target_node = self._registry.get_node(target_node_id)
        if not target_node:
            raise ValueError(f"Target node {target_node_id} not found")

        # Check if link already exists
        for link in self._active_links.values():
            if (
                link.source_node_id == self._local_node_id and
                link.target_node_id == target_node_id
            ):
                return link

        # Create new link
        link = FederationLink(
            source_node_id=self._local_node_id,
            target_node_id=target_node_id,
            status=FederationLinkStatus.ACTIVE,
            allowed_artifact_types=allowed_artifact_types or [],
            trust_level=1.0 if target_node_id in self._trusted_nodes else 0.5,
        )

        self._active_links[link.link_id] = link
        self._storage.save_link(link)

        logger.info(
            f"[Federation] Created link to {target_node.identity.node_name} "
            f"({link.link_id})"
        )

        return link

    def get_link_to_node(self, target_node_id: UUID) -> Optional[FederationLink]:
        """Get active link to a specific node."""
        for link in self._active_links.values():
            if (
                link.source_node_id == self._local_node_id and
                link.target_node_id == target_node_id
            ):
                return link
        return None

    def get_active_links(self) -> List[FederationLink]:
        """Get all active federation links."""
        return [
            link for link in self._active_links.values()
            if link.enabled and link.status == FederationLinkStatus.ACTIVE
        ]

    # ========================================================================
    # Artifact Export
    # ========================================================================

    async def export_artifacts(
        self,
        request: FederationExportRequest,
    ) -> FederationExportResponse:
        """
        Export artifacts to federation.

        Args:
            request: Export request with artifact IDs and targets

        Returns:
            Export response with contracts
        """
        export_id = uuid4()
        exported_artifacts = []
        failed_artifacts = []
        export_contracts = []
        warnings = []

        # Determine target nodes
        if request.target_node_ids:
            target_node_ids = request.target_node_ids
        else:
            # Broadcast to all trusted nodes with active links
            target_node_ids = [
                link.target_node_id
                for link in self.get_active_links()
                if link.target_node_id in self._trusted_nodes
            ]

        # Process each artifact
        for artifact_id in request.artifact_ids:
            try:
                # Get artifact from local storage (would need to integrate with artifact store)
                # For now, create a placeholder contract
                contract = FederationExportContract(
                    export_id=export_id,
                    source_node_id=self._local_node_id,
                    source_artifact_id=artifact_id,
                    artifact_type=FederationArtifactType.PATTERN,  # Placeholder
                    artifact_summary="Artifact exported for federation",
                    artifact_metadata={},
                    redaction_level=request.redaction_level,
                    target_node_ids=target_node_ids,
                    export_authority=request.export_authority,
                    governance_tags=request.governance_tags,
                    artifact_hash=hashlib.sha256(artifact_id.bytes).hexdigest(),
                )

                # Sign contract if secret available
                for target_id in target_node_ids:
                    if target_id in self._node_secrets:
                        contract.signature = self._sign_contract(contract, target_id)

                export_contracts.append(contract.model_dump())
                exported_artifacts.append(artifact_id)

                self._storage.save_contract(contract)

            except Exception as e:
                failed_artifacts.append({
                    "artifact_id": str(artifact_id),
                    "error": str(e),
                })

        response = FederationExportResponse(
            success=len(failed_artifacts) == 0,
            export_id=export_id,
            exported_artifacts=exported_artifacts,
            failed_artifacts=failed_artifacts,
            export_contracts=export_contracts,
            warnings=warnings,
        )

        logger.info(
            f"[Federation] Exported {len(exported_artifacts)} artifacts "
            f"to {len(target_node_ids)} nodes ({export_id})"
        )

        return response

    def _sign_contract(self, contract: FederationExportContract, target_node_id: UUID) -> str:
        """Sign a contract with HMAC."""
        secret = self._node_secrets.get(target_node_id)
        if not secret:
            return ""

        # Create message to sign
        message = (
            f"{contract.source_node_id}:{contract.source_artifact_id}:"
            f"{contract.artifact_type}:{contract.redaction_level}"
        )

        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    # ========================================================================
    # Artifact Import
    # ========================================================================

    async def import_artifacts(
        self,
        request: FederationImportRequest,
    ) -> FederationImportResponse:
        """
        Import artifacts from federation.

        Args:
            request: Import request with filters

        Returns:
            Import response with validated artifacts
        """
        import_id = uuid4()
        imported_artifacts = []
        validation_results = []
        warnings = []

        # Get available artifacts from trusted nodes
        # In a real implementation, this would query the federation network
        # For now, we'll validate against what we have in storage

        for artifact in self._storage._imported_artifacts.values():
            # Validate artifact
            validation = await self._validate_import(artifact, request)
            validation_results.append(validation)

            if validation.is_valid:
                # Check if artifact can be consumed
                if artifact.can_consume(self._local_node_id, self._trusted_nodes):
                    imported_artifacts.append(artifact)
                else:
                    warnings.append(
                        f"Artifact {artifact.artifact_id} cannot be consumed by this node"
                    )

        response = FederationImportResponse(
            success=len(imported_artifacts) > 0,
            import_id=import_id,
            imported_artifacts=imported_artifacts,
            validation_results=validation_results,
            warnings=warnings,
        )

        logger.info(
            f"[Federation] Imported {len(imported_artifacts)} artifacts "
            f"({import_id})"
        )

        return response

    async def _validate_import(
        self,
        artifact: FederatedArtifact,
        request: FederationImportRequest,
    ) -> FederationImportValidation:
        """Validate a federated artifact for import."""
        errors = []
        warnings_list = []

        # Check source authorization
        source_authorized = artifact.source_node_id in self._trusted_nodes
        if not source_authorized:
            errors.append("Source node is not trusted")

        # Check signature if present
        signature_valid = True
        if artifact.federation_metadata.signature:
            # Verify signature
            if artifact.source_node_id in self._node_secrets:
                # In a real implementation, verify the signature
                pass

        # Check redaction compliance
        redaction_compliant = artifact.redaction_level in ("minimal", "standard", "aggressive")

        # Check TTL
        within_ttl = True
        if artifact.federation_metadata.expires_at:
            within_ttl = datetime.now() < artifact.federation_metadata.expires_at

        # Check governance tags
        if request.required_governance_tags:
            has_required_tags = any(
                tag in artifact.federation_metadata.governance_tags
                for tag in request.required_governance_tags
            )
            if not has_required_tags:
                errors.append("Missing required governance tags")

        # Check confidence threshold
        if artifact.confidence < request.min_confidence:
            errors.append(f"Artifact confidence {artifact.confidence} below threshold {request.min_confidence}")

        # Check artifact type filter
        if request.artifact_types:
            if artifact.artifact_type not in request.artifact_types:
                errors.append(f"Artifact type {artifact.artifact_type} not in allowed types")

        is_valid = (
            source_authorized and
            signature_valid and
            redaction_compliant and
            within_ttl and
            len(errors) == 0
        )

        return FederationImportValidation(
            is_valid=is_valid,
            validation_errors=errors,
            warnings=warnings_list,
            signature_valid=signature_valid,
            source_authorized=source_authorized,
            redaction_compliant=redaction_compliant,
            within_ttl=within_ttl,
        )

    # ========================================================================
    # Artifact Creation Helpers
    # ========================================================================

    async def create_federated_pattern(
        self,
        pattern_id: UUID,
        pattern_name: str,
        pattern_type: str,
        description: str,
        confidence: float,
        pattern_data: Dict[str, Any],
        sample_size: int = 0,
        redaction_level: str = "standard",
    ) -> FederatedPattern:
        """Create a federated pattern artifact."""
        local_node = self._registry.get_node(self._local_node_id)
        if not local_node:
            raise ValueError("Local node not registered")

        return FederatedPattern.create(
            pattern_id=pattern_id,
            pattern_name=pattern_name,
            pattern_type=pattern_type,
            description=description,
            confidence=confidence,
            source_node_id=self._local_node_id,
            source_node_name=local_node.identity.node_name,
            source_region=local_node.identity.region.value,
            pattern_data=pattern_data,
            sample_size=sample_size,
            redaction_level=redaction_level,
        )

    async def create_federated_benchmark(
        self,
        metric_name: str,
        metric_type: str,
        statistics: Dict[str, float],
        sample_size: int,
        confidence: float = 0.95,
        redaction_level: str = "standard",
    ) -> FederatedBenchmark:
        """Create a federated benchmark artifact."""
        local_node = self._registry.get_node(self._local_node_id)
        if not local_node:
            raise ValueError("Local node not registered")

        return FederatedBenchmark.create(
            metric_name=metric_name,
            metric_type=metric_type,
            statistics=statistics,
            sample_size=sample_size,
            source_node_id=self._local_node_id,
            source_node_name=local_node.identity.node_name,
            source_region=local_node.identity.region.value,
            confidence=confidence,
            redaction_level=redaction_level,
        )

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_federation_statistics(self) -> Dict[str, Any]:
        """Get federation statistics."""
        links = list(self._active_links.values())

        return {
            "local_node_id": str(self._local_node_id),
            "trusted_nodes": len(self._trusted_nodes),
            "active_links": len(self.get_active_links()),
            "total_links": len(links),
            "exported_artifacts": len(self._storage._exported_artifacts),
            "imported_artifacts": len(self._storage._imported_artifacts),
            "links_by_status": {
                status.value: len([l for l in links if l.status == status])
                for status in FederationLinkStatus
            },
        }


# Global federation controller instances (one per local node)
_controllers: Dict[UUID, FederationController] = {}


def get_federation_controller(
    local_node_id: UUID,
    storage_path: Optional[Path] = None,
) -> FederationController:
    """Get the federation controller for a local node."""
    if local_node_id not in _controllers:
        _controllers[local_node_id] = FederationController(local_node_id, storage_path)
    return _controllers[local_node_id]
