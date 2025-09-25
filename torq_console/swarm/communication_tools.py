"""
Communication Tools for TORQ Console - Agency Swarm Compatible.

Provides send_message tool and related communication capabilities
for agents to communicate directly with each other.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from .message_system import message_system, MessagePriority
from .communication_parser import communication_parser


class CommunicationTools:
    """
    Communication tools for inter-agent messaging.

    Provides send_message tool compatible with Agency Swarm patterns
    and Claude Code tool interface standards.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def send_message(
        self,
        agent_id: str,
        target_agent: str,
        message: str,
        priority: str = 'normal',
        require_acknowledgment: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a message to another agent.

        Args:
            agent_id: ID of the sending agent
            target_agent: ID of the target agent
            message: Message content to send
            priority: Message priority (low, normal, high, critical)
            require_acknowledgment: Whether to require delivery acknowledgment
            **kwargs: Additional metadata for the message

        Returns:
            Dict with send result and message details
        """
        try:
            # Create and send message
            msg = await message_system.create_message(
                source_agent=agent_id,
                target_agent=target_agent,
                content=message,
                priority=priority,
                require_ack=require_acknowledgment,
                **kwargs
            )

            result = await message_system.send_message(msg)

            if result['success']:
                self.logger.info(f"Message sent from {agent_id} to {target_agent}: {msg.message_id}")
                return {
                    'success': True,
                    'message_id': msg.message_id,
                    'target_agent': target_agent,
                    'delivery_status': 'delivered',
                    'requires_ack': require_acknowledgment,
                    'priority': priority,
                    'sent_at': msg.created_at.isoformat(),
                    'expires_at': msg.expires_at.isoformat() if msg.expires_at else None
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown delivery error'),
                    'target_agent': target_agent,
                    'delivery_status': 'failed'
                }

        except Exception as e:
            self.logger.error(f"Error in send_message: {e}")
            return {
                'success': False,
                'error': str(e),
                'target_agent': target_agent,
                'delivery_status': 'error'
            }

    async def receive_messages(self, agent_id: str) -> Dict[str, Any]:
        """
        Receive all pending messages for an agent.

        Args:
            agent_id: ID of the receiving agent

        Returns:
            Dict with received messages and status
        """
        try:
            messages = await message_system.receive_messages(agent_id)

            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    'message_id': msg.message_id,
                    'from_agent': msg.source_agent,
                    'content': msg.content,
                    'priority': msg.priority.name,
                    'sent_at': msg.created_at.isoformat(),
                    'requires_ack': msg.require_ack,
                    'metadata': msg.metadata
                })

            self.logger.info(f"Retrieved {len(messages)} messages for {agent_id}")

            return {
                'success': True,
                'agent_id': agent_id,
                'message_count': len(messages),
                'messages': formatted_messages
            }

        except Exception as e:
            self.logger.error(f"Error receiving messages for {agent_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': agent_id,
                'message_count': 0,
                'messages': []
            }

    async def acknowledge_message(self, agent_id: str, message_id: str) -> Dict[str, Any]:
        """
        Acknowledge receipt of a message.

        Args:
            agent_id: ID of the acknowledging agent
            message_id: ID of the message to acknowledge

        Returns:
            Dict with acknowledgment status
        """
        try:
            success = await message_system.acknowledge_message(message_id, agent_id)

            if success:
                return {
                    'success': True,
                    'message_id': message_id,
                    'acknowledged_by': agent_id,
                    'status': 'acknowledged'
                }
            else:
                return {
                    'success': False,
                    'message_id': message_id,
                    'error': 'Message not found or already acknowledged',
                    'status': 'failed'
                }

        except Exception as e:
            self.logger.error(f"Error acknowledging message {message_id} by {agent_id}: {e}")
            return {
                'success': False,
                'message_id': message_id,
                'error': str(e),
                'status': 'error'
            }

    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific message.

        Args:
            message_id: ID of the message to check

        Returns:
            Dict with message status information
        """
        try:
            status = await message_system.get_message_status(message_id)

            if status:
                return {
                    'success': True,
                    'message_id': message_id,
                    'status': status['status'],
                    'created_at': status['created_at'],
                    'delivered_at': status['delivered_at'],
                    'acknowledged_at': status['acknowledged_at'],
                    'is_expired': status['is_expired'],
                    'retry_count': status['retry_count']
                }
            else:
                return {
                    'success': False,
                    'message_id': message_id,
                    'error': 'Message not found'
                }

        except Exception as e:
            self.logger.error(f"Error getting status for message {message_id}: {e}")
            return {
                'success': False,
                'message_id': message_id,
                'error': str(e)
            }

    async def broadcast_message(
        self,
        agent_id: str,
        target_agents: List[str],
        message: str,
        priority: str = 'normal',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a message to multiple agents.

        Args:
            agent_id: ID of the sending agent
            target_agents: List of target agent IDs
            message: Message content to broadcast
            priority: Message priority
            **kwargs: Additional metadata

        Returns:
            Dict with broadcast results
        """
        results = {
            'success': True,
            'sender': agent_id,
            'target_count': len(target_agents),
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'delivery_results': {}
        }

        for target_agent in target_agents:
            try:
                result = await self.send_message(
                    agent_id=agent_id,
                    target_agent=target_agent,
                    message=message,
                    priority=priority,
                    **kwargs
                )

                results['delivery_results'][target_agent] = result

                if result['success']:
                    results['successful_deliveries'] += 1
                else:
                    results['failed_deliveries'] += 1

            except Exception as e:
                results['delivery_results'][target_agent] = {
                    'success': False,
                    'error': str(e)
                }
                results['failed_deliveries'] += 1

        # Overall success if at least one delivery succeeded
        results['success'] = results['successful_deliveries'] > 0

        self.logger.info(f"Broadcast from {agent_id}: {results['successful_deliveries']}/{len(target_agents)} delivered")

        return results

    async def get_pending_count(self, agent_id: str) -> Dict[str, Any]:
        """
        Get count of pending messages for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Dict with pending message count
        """
        try:
            count = await message_system.get_agent_message_count(agent_id)

            return {
                'success': True,
                'agent_id': agent_id,
                'pending_messages': count
            }

        except Exception as e:
            self.logger.error(f"Error getting pending count for {agent_id}: {e}")
            return {
                'success': False,
                'agent_id': agent_id,
                'error': str(e),
                'pending_messages': 0
            }

    async def parse_directional_command(self, content: str, current_agent: str) -> Dict[str, Any]:
        """
        Parse and execute directional communication commands.

        Args:
            content: Content that may contain directional syntax
            current_agent: Agent executing the command

        Returns:
            Dict with parsing and execution results
        """
        try:
            # Check for directional syntax
            if not communication_parser.has_directional_syntax(content):
                return {
                    'success': True,
                    'has_directional_syntax': False,
                    'base_query': content,
                    'messages_sent': 0
                }

            # Parse directional messages
            messages = communication_parser.parse_directional_syntax(content)
            base_query = communication_parser.extract_base_query(content)

            results = {
                'success': True,
                'has_directional_syntax': True,
                'base_query': base_query,
                'messages_parsed': len(messages),
                'messages_sent': 0,
                'send_results': []
            }

            # Send each parsed message
            for msg in messages:
                for target_agent in msg.target_agents:
                    send_result = await self.send_message(
                        agent_id=msg.source_agent,
                        target_agent=target_agent,
                        message=msg.message_content,
                        priority=msg.priority,
                        require_acknowledgment=msg.require_ack,
                        **(msg.metadata or {})
                    )

                    results['send_results'].append({
                        'source': msg.source_agent,
                        'target': target_agent,
                        'result': send_result
                    })

                    if send_result['success']:
                        results['messages_sent'] += 1

            return results

        except Exception as e:
            self.logger.error(f"Error parsing directional command: {e}")
            return {
                'success': False,
                'error': str(e),
                'has_directional_syntax': False,
                'base_query': content,
                'messages_sent': 0
            }

    async def get_communication_stats(self) -> Dict[str, Any]:
        """
        Get overall communication system statistics.

        Returns:
            Dict with communication statistics
        """
        try:
            stats = await message_system.get_communication_stats()

            return {
                'success': True,
                'system_stats': stats,
                'system_status': 'operational'
            }

        except Exception as e:
            self.logger.error(f"Error getting communication stats: {e}")
            return {
                'success': False,
                'error': str(e),
                'system_status': 'error'
            }


# Export communication tools instance
communication_tools = CommunicationTools()

async def send_agent_message(
    agent_id: str,
    target_agent: str,
    message: str,
    priority: str = 'normal',
    require_acknowledgment: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for sending messages between agents.
    Compatible with Agency Swarm send_message tool interface.
    """
    return await communication_tools.send_message(
        agent_id, target_agent, message, priority, require_acknowledgment, **kwargs
    )