/**
 * New Workflow Page
 *
 * Create a new workflow from template, AI generation, or from scratch.
 */

import { Suspense, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useWorkflowTemplates, useCreateWorkflow } from "../../features/workflows";
import { TemplateGallery, WorkflowEditor } from "../../features/workflows/components";
import { WorkflowPromptBuilder } from "../../features/workflows/components/WorkflowPromptBuilder";
import { WorkflowDraftPreview } from "../../features/workflows/components/WorkflowDraftPreview";
import { workflowPlannerApi } from "../../features/workflows/api/workflowPlannerApi";
import type { WorkflowDraft } from "../../features/workflows/api/workflowPlannerApi";
import { ArrowLeft, Sparkles, Wand2 } from "lucide-react";

type CreationStep = "template" | "ai-generate" | "ai-preview" | "editor";

function NewWorkflowPageContent() {
  const navigate = useNavigate();
  const { data: templatesData, isLoading: templatesLoading } = useWorkflowTemplates();
  const createWorkflowMutation = useCreateWorkflow();

  const [step, setStep] = useState<CreationStep>("template");
  const [activeTab, setActiveTab] = useState<"templates" | "ai">("templates");
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [generatedDraft, setGeneratedDraft] = useState<WorkflowDraft | null>(null);

  const handleSelectTemplate = (template: any) => {
    setSelectedTemplate(template);
    setStep("editor");
  };

  const handleCreateFromScratch = () => {
    setSelectedTemplate(null);
    setStep("editor");
  };

  const handleAIDraftGenerated = (draft: WorkflowDraft) => {
    setGeneratedDraft(draft);
    setStep("ai-preview");
  };

  const handleAIDiscard = () => {
    setGeneratedDraft(null);
    setStep("ai-generate");
  };

  const handleAIEdit = (draft: WorkflowDraft) => {
    // Convert draft to editor format and go to editor
    setSelectedTemplate({
      name: draft.name,
      description: draft.description,
      nodes: draft.nodes.map((node) => ({
        node_id: node.node_key,
        node_key: node.node_key,
        name: node.name,
        node_type: node.node_type,
        agent_id: node.agent_id,
        depends_on: node.depends_on,
        parameters: node.parameters,
        timeout_seconds: node.timeout_seconds,
        retry_policy: node.retry_policy,
        position_x: 100,
        position_y: 0,
      })),
      edges: draft.edges.map((edge) => ({
        edge_id: `${edge.source_node_key}-${edge.target_node_key}`,
        source_node_id: edge.source_node_key,
        target_node_id: edge.target_node_key,
      })),
    });
    setStep("editor");
  };

  const handleAISaveWorkflow = async (draft: WorkflowDraft) => {
    try {
      const createRequest = workflowPlannerApi.draftToCreateRequest(draft);
      await createWorkflowMutation.mutateAsync(createRequest);
      navigate("/workflows");
    } catch (error) {
      console.error("Failed to create workflow:", error);
      alert("Failed to create workflow. Please try again.");
    }
  };

  const handleSaveWorkflow = async (workflow: any) => {
    try {
      await createWorkflowMutation.mutateAsync(workflow);
      navigate("/workflows");
    } catch (error) {
      console.error("Failed to create workflow:", error);
      alert("Failed to create workflow. Please try again.");
    }
  };

  // Tab switching
  const handleTabChange = (tab: "templates" | "ai") => {
    setActiveTab(tab);
    if (tab === "templates") {
      setStep("template");
    } else {
      setStep("ai-generate");
    }
  };

  if (templatesLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          {step === "editor" && (
            <button
              onClick={() => setStep("template")}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          {step === "ai-preview" && (
            <button
              onClick={() => setStep("ai-generate")}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Create Workflow</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {step === "template" || step === "ai-generate"
                ? "Choose how to create your workflow"
                : step === "ai-preview"
                ? "Review your AI-generated workflow"
                : "Configure your workflow"}
            </p>
          </div>
        </div>
      </div>

      {/* Tab Selection (only shown on initial steps) */}
      {(step === "template" || step === "ai-generate") && (
        <div className="px-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex gap-6">
            <button
              onClick={() => handleTabChange("templates")}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "templates"
                  ? "border-purple-500 text-purple-600 dark:text-purple-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
              }`}
            >
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                Templates
              </div>
            </button>
            <button
              onClick={() => handleTabChange("ai")}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === "ai"
                  ? "border-purple-500 text-purple-600 dark:text-purple-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
              }`}
            >
              <div className="flex items-center gap-2">
                <Wand2 className="w-4 h-4" />
                Generate with AI
              </div>
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {step === "template" && activeTab === "templates" && (
          <div className="h-full overflow-y-auto p-6">
            {/* Quick Start Banner */}
            <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/40 rounded-lg">
                  <Sparkles className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">Quick Start</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Choose a template to get started quickly, or build from scratch.</p>
                </div>
              </div>
            </div>

            <TemplateGallery
              templates={templatesData?.examples || []}
              onSelectTemplate={handleSelectTemplate}
            />

            {/* Start from Scratch Card */}
            <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-6">
              <button
                onClick={handleCreateFromScratch}
                className="w-full text-left p-6 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
              >
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                    <Sparkles className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Start from Scratch</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Build a custom workflow with full control</p>
                  </div>
                </div>
              </button>
            </div>
          </div>
        )}

        {step === "ai-generate" && activeTab === "ai" && (
          <WorkflowPromptBuilder
            onDraftGenerated={handleAIDraftGenerated}
            className="h-full"
          />
        )}

        {step === "ai-preview" && generatedDraft && (
          <WorkflowDraftPreview
            draft={generatedDraft}
            onSave={handleAISaveWorkflow}
            onEdit={handleAIEdit}
            onDiscard={handleAIDiscard}
            className="h-full"
          />
        )}

        {step === "editor" && (
          <WorkflowEditor
            initialNodes={selectedTemplate?.nodes || []}
            initialEdges={selectedTemplate?.edges || []}
            onSave={handleSaveWorkflow}
            onCancel={() => navigate("/workflows")}
            className="h-full"
          />
        )}
      </div>
    </div>
  );
}

function LoadingScreen() {
  return (
    <div className="h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-gray-100" />
    </div>
  );
}

export function NewWorkflowPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <NewWorkflowPageContent />
    </Suspense>
  );
}

export default function NewWorkflowPageWrapper() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <NewWorkflowPage />
    </Suspense>
  );
}
