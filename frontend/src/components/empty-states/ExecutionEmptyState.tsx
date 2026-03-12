/**
 * Phase 3: Product UX & Identity
 *
 * Empty State Component for Executions Page
 * Shown when user has no workflow executions yet
 */

import { Link } from 'react-router-dom';
import { Play, Clock, TrendingUp, Activity, Zap } from 'lucide-react';

interface ExecutionEmptyStateProps {
  onCreateWorkflow?: () => void;
}

export function ExecutionEmptyState({ onCreateWorkflow }: ExecutionEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-8 py-12">
      {/* Icon */}
      <div className="w-20 h-20 bg-gradient-to-br from-green-100 to-teal-100 rounded-full flex items-center justify-center mb-6">
        <Activity className="w-10 h-10 text-green-600" />
      </div>

      {/* Heading */}
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        No executions yet
      </h2>
      <p className="text-gray-500 text-center max-w-md mb-8">
        Workflow executions will appear here once you run a workflow.
        Track progress, view outputs, and inspect results in real-time.
      </p>

      {/* Feature Highlights */}
      <div className="grid grid-cols-3 gap-6 max-w-2xl w-full mb-8">
        <FeatureCard
          icon={<Play className="w-5 h-5" />}
          title="Manual Trigger"
          description="Run workflows on-demand from the Workflows page"
        />
        <FeatureCard
          icon={<Clock className="w-5 h-5" />}
          title="Scheduled Runs"
          description="Set up recurring workflows for daily tasks"
        />
        <FeatureCard
          icon={<TrendingUp className="w-5 h-5" />}
          title="Live Monitoring"
          description="Watch executions progress in real-time"
        />
      </div>

      {/* CTA */}
      <div className="flex flex-col items-center gap-3">
        {onCreateWorkflow ? (
          <button
            onClick={onCreateWorkflow}
            className="inline-flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium shadow-sm hover:shadow-md"
          >
            <Zap className="w-5 h-5 mr-2" />
            Create a Workflow to Run
          </button>
        ) : (
          <Link
            to="/workflows/new"
            className="inline-flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium shadow-sm hover:shadow-md"
          >
            <Zap className="w-5 h-5 mr-2" />
            Create a Workflow to Run
          </Link>
        )}
        <p className="text-sm text-gray-400">
          Or run an existing workflow from the Workflows page
        </p>
      </div>

      {/* How it works */}
      <div className="mt-12 p-6 bg-gray-50 rounded-xl max-w-2xl">
        <h3 className="font-semibold text-gray-900 mb-4 text-center">How Executions Work</h3>
        <div className="flex items-center justify-between">
          {[
            { label: 'Create Workflow', desc: 'Design your agent workflow' },
            { label: 'Trigger Run', desc: 'Manual or scheduled' },
            { label: 'Monitor Progress', desc: 'Real-time updates' },
            { label: 'View Results', desc: 'Inspect outputs' },
          ].map((step, i) => (
            <div key={i} className="flex-1 text-center">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
                <span className="text-blue-600 font-semibold text-sm">{i + 1}</span>
              </div>
              <p className="text-sm font-medium text-gray-900">{step.label}</p>
              <p className="text-xs text-gray-500">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="text-center">
      <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-3 text-gray-600">
        {icon}
      </div>
      <h3 className="font-medium text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500">{description}</p>
    </div>
  );
}
