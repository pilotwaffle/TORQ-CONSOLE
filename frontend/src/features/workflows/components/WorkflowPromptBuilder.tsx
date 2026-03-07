/**
 * WorkflowPromptBuilder Component
 *
 * UI for entering natural language prompts to generate workflows.
 */

import { useState } from "react";
import { Wand2, Loader2, AlertCircle } from "lucide-react";
import { useDraftWorkflow } from "@workflows/hooks/useDraftWorkflow";
import type { WorkflowPlannerResponse } from "@workflows/api/workflowPlannerApi";

interface WorkflowPromptBuilderProps {
  onDraftGenerated: (draft: WorkflowPlannerResponse["draft"]) => void;
  className?: string;
}

export function WorkflowPromptBuilder({ onDraftGenerated, className = "" }: WorkflowPromptBuilderProps) {
  const [prompt, setPrompt] = useState("");
  const mutation = useDraftWorkflow();

  const isGenerating = mutation.isPending;
  const error = mutation.error;

  const handleGenerate = async () => {
    if (!prompt.trim() || prompt.length < 10) {
      return;
    }

    try {
      const result = await mutation.mutateAsync({ prompt });

      if (result.success && result.draft) {
        onDraftGenerated(result.draft);
        // Clear prompt on success
        setPrompt("");
      }
    } catch (err) {
      // Error is handled via mutation.error
      console.error("Failed to generate workflow:", err);
    }
  };

  const examplePrompts = [
    "Research the AI infrastructure market and create a strategic summary",
    "Analyze competitors in the AI space and generate insights",
    "Research a company and produce a consulting summary",
    "Gather market data and synthesize into an executive report",
  ];

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <Wand2 className="w-5 h-5 text-purple-500" />
          Generate Workflow with AI
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Describe what you want to automate, and TORQ will design a workflow for you.
        </p>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Prompt Input */}
        <div className="mb-6">
          <label htmlFor="workflow-prompt" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Describe your workflow
          </label>
          <textarea
            id="workflow-prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Example: Research the AI market, analyze competitors, and create a strategic summary..."
            className="w-full h-32 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
            disabled={isGenerating}
          />
          <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {prompt.length} / 4000 characters
            </span>
            <span className={`text-xs ${prompt.length >= 10 ? "text-green-600 dark:text-green-400" : "text-gray-400"}`}>
              {prompt.length >= 10 ? "Ready to generate" : "Minimum 10 characters"}
            </span>
          </div>
        </div>

        {/* Example Prompts */}
        <div className="mb-6">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Try an example:
          </p>
          <div className="grid grid-cols-1 gap-2">
            {examplePrompts.map((example, index) => (
              <button
                key={index}
                onClick={() => setPrompt(example)}
                disabled={isGenerating}
                className="text-left px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                "{example}"
              </button>
            ))}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800 dark:text-red-300">
                Failed to generate workflow
              </p>
              <p className="text-sm text-red-700 dark:text-red-400 mt-1">
                {error.message || "An unexpected error occurred. Please try again."}
              </p>
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <p className="text-sm text-blue-800 dark:text-blue-300">
            <strong>Note:</strong> Generated workflows are drafts only. You can review and edit nodes, connections, and settings before saving.
          </p>
        </div>
      </div>

      {/* Footer - Generate Button */}
      <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={handleGenerate}
          disabled={isGenerating || prompt.length < 10}
          className="w-full py-3 px-4 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white font-medium rounded-lg flex items-center justify-center gap-2 transition-colors disabled:cursor-not-allowed"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Generating workflow...
            </>
          ) : (
            <>
              <Wand2 className="w-5 h-5" />
              Generate Workflow
            </>
          )}
        </button>
      </div>
    </div>
  );
}
