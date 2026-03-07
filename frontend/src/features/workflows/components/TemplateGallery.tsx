/**
 * Template Gallery Component
 *
 * Displays available workflow templates for quick start.
 */

import { useState } from "react";
import { Search, Zap, FileText, Globe, Code, Database, ArrowRight } from "lucide-react";
import type { WorkflowTemplate } from "@workflows/api";

interface TemplateGalleryProps {
  templates: WorkflowTemplate[];
  onSelectTemplate: (template: WorkflowTemplate) => void;
  isLoading?: boolean;
  className?: string;
}

const templateIcons: Record<string, React.ElementType> = {
  research: Search,
  web_scraping: Globe,
  code_generation: Code,
  data_processing: Database,
  analysis: Zap,
  default: FileText,
};

export function TemplateGallery({
  templates,
  onSelectTemplate,
  isLoading = false,
  className = "",
}: TemplateGalleryProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const filteredTemplates = templates.filter((template) => {
    const matchesSearch =
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory = !selectedCategory || template.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  const categories = Array.from(new Set(templates.map((t) => t.category || "default")));

  if (isLoading) {
    return (
      <div className="template-gallery-loading flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  return (
    <div className={`template-gallery ${className}`}>
      {/* Search and Filters */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Category Pills */}
        <div className="flex gap-2 mt-3 overflow-x-auto pb-2">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-3 py-1 rounded-full text-sm whitespace-nowrap transition ${
              !selectedCategory
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            All Templates
          </button>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1 rounded-full text-sm whitespace-nowrap capitalize transition ${
                selectedCategory === category
                  ? "bg-gray-900 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Template Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTemplates.map((template) => {
          const Icon = templateIcons[template.id] || templateIcons.default;

          return (
            <button
              key={template.id}
              onClick={() => onSelectTemplate(template)}
              className="text-left group bg-white border border-gray-200 rounded-lg p-5 hover:border-gray-400 hover:shadow-md transition-all"
            >
              {/* Icon & Name */}
              <div className="flex items-start justify-between mb-3">
                <div className="p-2 bg-gray-100 rounded-lg group-hover:bg-blue-50 transition">
                  <Icon className="w-5 h-5 text-gray-700 group-hover:text-blue-600 transition" />
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition" />
              </div>

              {/* Name */}
              <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition">
                {template.name}
              </h3>

              {/* Description */}
              <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                {template.description}
              </p>

              {/* Stats */}
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 rounded bg-gray-200 flex items-center justify-center">
                    <span className="text-[10px] font-bold">{template.nodes?.length ?? 0}</span>
                  </div>
                  nodes
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-4 h-4 rounded bg-gray-200 flex items-center justify-center">
                    <span className="text-[10px] font-bold">{template.edges?.length ?? 0}</span>
                  </div>
                  edges
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No templates found</h3>
          <p className="text-gray-500">Try adjusting your search or filters</p>
        </div>
      )}
    </div>
  );
}
