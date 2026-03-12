/**
 * Phase 3: Product UX & Identity
 *
 * Empty State Component for Workflows Page
 * Shown when user has no workflows yet - now with seeded workflow templates
 */

import { Link, useNavigate } from 'react-router-dom';
import { Plus, Sparkles, FileCode, Zap, Users, Workflow, Database, MessageSquare, TrendingUp } from 'lucide-react';
import { SEEDED_WORKFLOWS } from '@/features/workflows/data/seededWorkflows';

interface WorkflowEmptyStateProps {
  onCreateWorkflow?: () => void;
}

const TEMPLATE_ICONS: Record<string, React.ReactNode> = {
  'development': <FileCode className="w-5 h-5" />,
  'research': <Sparkles className="w-5 h-5" />,
  'productivity': <Zap className="w-5 h-5" />,
  'data': <Database className="w-5 h-5" />,
  'support': <MessageSquare className="w-5 h-5" />,
  'marketing': <TrendingUp className="w-5 h-5" />,
};

const COMPLEXITY_BADGES = {
  'beginner': { label: 'Beginner', color: 'bg-green-100 text-green-700' },
  'intermediate': { label: 'Intermediate', color: 'bg-blue-100 text-blue-700' },
  'advanced': { label: 'Advanced', color: 'bg-purple-100 text-purple-700' },
};

export function WorkflowEmptyState({ onCreateWorkflow }: WorkflowEmptyStateProps) {
  const navigate = useNavigate();

  const handleTemplateClick = (templateId: string) => {
    // Navigate to workflow builder with template
    navigate(`/workflows/new?template=${templateId}`);
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-8 py-12">
      {/* Icon */}
      <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mb-6">
        <Workflow className="w-10 h-10 text-blue-600" />
      </div>

      {/* Heading */}
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        No workflows yet
      </h2>
      <p className="text-gray-500 text-center max-w-md mb-8">
        Create automated workflows that chain multiple AI agents together.
        Start from scratch or use a template.
      </p>

      {/* Seeded Template Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl w-full mb-8">
        {SEEDED_WORKFLOWS.slice(0, 6).map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            onClick={() => handleTemplateClick(template.id)}
          />
        ))}
      </div>

      {/* CTA */}
      <div className="flex flex-col items-center gap-3">
        {onCreateWorkflow ? (
          <button
            onClick={onCreateWorkflow}
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm hover:shadow-md"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create Your First Workflow
          </button>
        ) : (
          <Link
            to="/workflows/new"
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm hover:shadow-md"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create Your First Workflow
          </Link>
        )}
        <p className="text-sm text-gray-400">
          Or click a template above to get started
        </p>
      </div>
    </div>
  );
}

interface TemplateCardProps {
  template: {
    id: string;
    name: string;
    description: string;
    category?: string;
    config?: {
      estimated_duration?: string;
      complexity?: 'beginner' | 'intermediate' | 'advanced';
      tags?: string[];
    };
  };
  onClick: () => void;
}

function TemplateCard({ template, onClick }: TemplateCardProps) {
  const complexity = template.config?.complexity || 'beginner';
  const badge = COMPLEXITY_BADGES[complexity];
  const icon = TEMPLATE_ICONS[template.category?.toLowerCase() || 'development'] || <Sparkles className="w-5 h-5" />;

  return (
    <button
      onClick={onClick}
      className="relative p-4 border border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-sm transition-all bg-white text-left group"
    >
      {/* Category Icon */}
      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center mb-3 text-gray-600 group-hover:bg-blue-100 group-hover:text-blue-600 transition-colors">
        {icon}
      </div>

      {/* Complexity Badge */}
      <div className="absolute top-3 right-3">
        <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${badge.color}`}>
          {badge.label}
        </span>
      </div>

      {/* Title & Description */}
      <h3 className="font-semibold text-gray-900 mb-1">{template.name}</h3>
      <p className="text-sm text-gray-500 mb-3 line-clamp-2">{template.description}</p>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>{template.config?.estimated_duration || '5-10 min'}</span>
        {template.category && (
          <span className="capitalize">{template.category}</span>
        )}
      </div>

      {/* Tags */}
      {template.config?.tags && template.config.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {template.config.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}
