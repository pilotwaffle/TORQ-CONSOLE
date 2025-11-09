"""
n8n Workflow Architect Agent - Usage Examples

This file demonstrates how to use the n8n Workflow Architect Agent
to design and generate production-ready n8n workflow JSON configurations.
"""

import asyncio
import json
import os
from pathlib import Path

# Import the n8n architect agent
from torq_console.agents import (
    create_n8n_architect_agent,
    WorkflowRequirements,
    WorkflowTriggerType,
    ErrorHandlingStrategy
)


async def example_1_requirements_discovery():
    """
    Example 1: Requirements Discovery Phase

    Start with a simple request and let the agent ask targeted questions
    to extract complete specifications.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Requirements Discovery")
    print("=" * 80 + "\n")

    # Create the agent
    agent = create_n8n_architect_agent()

    # Initial request
    initial_request = """
    I need a workflow that receives webhook notifications from GitHub
    when pull requests are created or updated, then posts a summary
    to our Slack channel.
    """

    # Phase 1: Requirements Discovery
    result = await agent.discover_requirements(initial_request)

    if result['success']:
        print("Agent's Response:")
        print("-" * 80)
        print(result['response'])
        print("-" * 80)
        print("\nNext Action:", result['next_action'])
    else:
        print(f"Error: {result['error']}")


async def example_2_full_workflow_payment_processor():
    """
    Example 2: Complete Payment Processing Workflow

    Create a production-ready payment processing workflow with:
    - Webhook trigger with HMAC signature validation
    - Stripe API integration
    - Database writes
    - Error handling with retries
    - Slack notifications
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Payment Processing Workflow")
    print("=" * 80 + "\n")

    # Create the agent
    agent = create_n8n_architect_agent()

    # Define complete requirements
    requirements = WorkflowRequirements(
        name="stripe_payment_processor",
        purpose="Process Stripe payment webhooks with validation, database storage, and notifications",
        trigger_type=WorkflowTriggerType.WEBHOOK,
        error_handling=ErrorHandlingStrategy.HARD_FAIL,
        data_sources=[
            "Stripe Webhook",
            "Stripe API",
            "PostgreSQL Database",
            "Slack API"
        ],
        security_requirements=[
            "HMAC-SHA256 signature validation",
            "API key authentication",
            "Input validation against JSON schema"
        ],
        expected_volume="medium",  # 100-10K/day
        outputs=[
            "Database record (payments table)",
            "Slack notification to #payments channel",
            "Success/failure webhook response"
        ],
        constraints={
            "latency": "< 2 seconds",
            "compliance": "PCI-DSS",
            "retry_attempts": 3
        }
    )

    # Execute full workflow creation
    print("Creating workflow with complete requirements...")
    result = await agent.full_workflow_creation(
        request="Create Stripe payment processing workflow",
        requirements=requirements
    )

    if result['success']:
        workflow_json = result['workflow_json']
        metadata = result['metadata']

        print(f"\n✅ Workflow Generated Successfully!")
        print(f"   - Workflow ID: {metadata['workflow_id']}")
        print(f"   - Node Count: {metadata['node_count']}")
        print(f"   - Created At: {metadata['created_at']}")

        # Save to file
        output_file = Path("stripe_payment_processor.json")
        with open(output_file, 'w') as f:
            json.dump(workflow_json, f, indent=2)

        print(f"\n📁 Workflow saved to: {output_file}")
        print("\n📋 Workflow Metadata:")
        print(f"   - Name: {workflow_json['name']}")
        print(f"   - Version: {workflow_json['meta']['version']}")
        print(f"   - Template Creator: {workflow_json['meta']['templateCreatedBy']}")

        if 'requiredEnvVars' in workflow_json['meta']:
            print(f"\n🔐 Required Environment Variables:")
            for env_var in workflow_json['meta']['requiredEnvVars']:
                print(f"   - {env_var}")

    else:
        print(f"\n❌ Workflow generation failed: {result.get('error')}")


async def example_3_user_onboarding_workflow():
    """
    Example 3: User Onboarding Automation

    Create a user onboarding workflow with:
    - Scheduled trigger (runs daily)
    - Auth0 integration
    - SendGrid email
    - CRM updates
    - Retry logic with exponential backoff
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: User Onboarding Automation")
    print("=" * 80 + "\n")

    agent = create_n8n_architect_agent()

    requirements = WorkflowRequirements(
        name="user_onboarding_automation",
        purpose="Automated daily user onboarding workflow with email, CRM updates, and team notifications",
        trigger_type=WorkflowTriggerType.SCHEDULE,
        error_handling=ErrorHandlingStrategy.RETRY_BACKOFF,
        data_sources=[
            "Auth0 API",
            "SendGrid API",
            "Salesforce CRM",
            "Slack API"
        ],
        security_requirements=[
            "OAuth 2.0 for Auth0",
            "API keys for SendGrid and Salesforce",
            "Rate limiting (100 req/min)"
        ],
        expected_volume="high",  # >10K/day
        outputs=[
            "Welcome emails via SendGrid",
            "CRM contact creation",
            "Slack notifications to #growth",
            "Daily summary report"
        ],
        constraints={
            "schedule": "0 9 * * *",  # 9 AM daily
            "batch_size": 100,
            "timeout": 30  # seconds per user
        }
    )

    # Design blueprint only (don't generate JSON yet)
    print("Designing workflow blueprint...")
    blueprint = await agent.design_blueprint(requirements)

    print("\n📐 Workflow Blueprint Created:")
    print(f"   - Name: {blueprint.metadata['name']}")
    print(f"   - Purpose: {blueprint.metadata['purpose']}")
    print(f"   - Trigger: {blueprint.metadata['trigger_type']}")
    print(f"\n📊 Error Handling:")
    print(f"   - Strategy: {blueprint.error_handling_strategy['type']}")
    print(f"   - Retry Enabled: {blueprint.error_handling_strategy['retry_enabled']}")
    print(f"\n🔒 Security Measures:")
    for measure in blueprint.security_measures:
        print(f"   - {measure}")

    # Now generate the JSON
    print("\n🔧 Generating workflow JSON...")
    result = await agent.generate_workflow_json(blueprint)

    if result['success']:
        output_file = Path("user_onboarding_automation.json")
        with open(output_file, 'w') as f:
            json.dump(result['workflow_json'], f, indent=2)

        print(f"\n✅ Workflow JSON generated and saved to: {output_file}")
        print(f"   - Import this file into n8n to use the workflow")


async def example_4_api_integration_workflow():
    """
    Example 4: Multi-API Integration Workflow

    Create a workflow that integrates multiple APIs:
    - Webhook trigger
    - OpenAI API for content analysis
    - Airtable for data storage
    - Twitter API for posting
    - Comprehensive error handling
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Multi-API Integration Workflow")
    print("=" * 80 + "\n")

    agent = create_n8n_architect_agent()

    requirements = WorkflowRequirements(
        name="content_analysis_and_publish",
        purpose="Receive content via webhook, analyze with AI, store in Airtable, and publish to Twitter",
        trigger_type=WorkflowTriggerType.WEBHOOK,
        error_handling=ErrorHandlingStrategy.SOFT_FAIL,
        data_sources=[
            "Webhook (incoming content)",
            "OpenAI API (GPT-4)",
            "Airtable API",
            "Twitter API v2"
        ],
        security_requirements=[
            "Webhook HMAC validation",
            "OpenAI API key",
            "Airtable OAuth",
            "Twitter OAuth 2.0"
        ],
        expected_volume="low",  # <100/day
        outputs=[
            "AI analysis results",
            "Airtable record",
            "Twitter post",
            "Success metrics log"
        ],
        constraints={
            "ai_model": "gpt-4-turbo",
            "max_content_length": 5000,
            "twitter_character_limit": 280
        }
    )

    result = await agent.full_workflow_creation(
        request="Multi-API integration workflow",
        requirements=requirements
    )

    if result['success']:
        output_file = Path("content_analysis_and_publish.json")
        with open(output_file, 'w') as f:
            json.dump(result['workflow_json'], f, indent=2)

        print(f"\n✅ Multi-API workflow created: {output_file}")
        print(f"   - Node Count: {result['metadata']['node_count']}")
        print("\n📝 Workflow includes:")
        print("   1. Webhook trigger with HMAC validation")
        print("   2. OpenAI content analysis")
        print("   3. Airtable data storage")
        print("   4. Twitter post publishing")
        print("   5. Comprehensive error handling")


async def example_5_sub_workflow_pattern():
    """
    Example 5: Sub-Workflow Pattern

    Create a reusable sub-workflow that can be called from other workflows.
    This is useful for common operations like sending notifications,
    logging events, or data transformations.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Reusable Sub-Workflow")
    print("=" * 80 + "\n")

    agent = create_n8n_architect_agent()

    requirements = WorkflowRequirements(
        name="notification_dispatcher",
        purpose="Reusable sub-workflow for sending multi-channel notifications (Email, Slack, SMS)",
        trigger_type=WorkflowTriggerType.SUB_WORKFLOW,
        error_handling=ErrorHandlingStrategy.SOFT_FAIL,
        data_sources=[
            "SendGrid (Email)",
            "Slack API",
            "Twilio (SMS)"
        ],
        security_requirements=[
            "API keys for all services",
            "Input validation"
        ],
        expected_volume="medium",
        outputs=[
            "Email sent confirmation",
            "Slack message ID",
            "SMS delivery status",
            "Aggregated delivery report"
        ],
        constraints={
            "idempotent": True,
            "timeout": 10,  # seconds
            "clear_input_output_contracts": True
        }
    )

    result = await agent.full_workflow_creation(
        request="Reusable notification sub-workflow",
        requirements=requirements
    )

    if result['success']:
        output_file = Path("notification_dispatcher_subworkflow.json")
        with open(output_file, 'w') as f:
            json.dump(result['workflow_json'], f, indent=2)

        print(f"\n✅ Sub-workflow created: {output_file}")
        print("\n📋 Sub-Workflow Features:")
        print("   - Can be called from any parent workflow")
        print("   - Idempotent design (safe to re-run)")
        print("   - Clear input/output contracts")
        print("   - Multi-channel notification support")
        print("   - Soft-fail error handling (logs errors, continues)")


async def example_6_agent_info():
    """
    Example 6: Get Agent Information

    Retrieve information about the n8n architect agent's capabilities.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Agent Information")
    print("=" * 80 + "\n")

    agent = create_n8n_architect_agent()
    info = agent.get_agent_info()

    print("📊 n8n Workflow Architect Agent")
    print("-" * 80)
    print(f"Name: {info['name']}")
    print(f"Version: {info['version']}")
    print(f"Type: {info['type']}")
    print(f"Model: {info['model']}")
    print(f"\nDescription:")
    print(f"  {info['description']}")
    print(f"\nCapabilities:")
    for capability in info['capabilities']:
        print(f"  - {capability}")
    print(f"\nWorkflow Phases:")
    for i, phase in enumerate(info['phases'], 1):
        print(f"  {i}. {phase}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("n8n Workflow Architect Agent - Examples")
    print("=" * 80)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  WARNING: No API key configured!")
        print("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable")
        print("   to run these examples.\n")
        return

    # Run examples
    await example_6_agent_info()
    await example_1_requirements_discovery()
    await example_2_full_workflow_payment_processor()
    await example_3_user_onboarding_workflow()
    await example_4_api_integration_workflow()
    await example_5_sub_workflow_pattern()

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
