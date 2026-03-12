/**
 * Operator Control Surface - Mission Portfolio Table
 *
 * Mission Portfolio Panel component showing all missions with status,
 * progress, and filtering. This is the entry point for the control surface.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type {
  MissionListItem,
  MissionStatus,
  MissionType,
  MissionListFilters,
} from "../types/mission";
import { useControlMissions } from "../hooks/useControlMissions";
import {
  formatDateTime,
  formatRelativeTime,
  formatProgressPercent,
  formatProgressCount,
  getStatusBadgeStyle,
  truncateText,
  formatMissionType,
} from "../utils/formatters";

// ============================================================================
// Types
// ============================================================================

interface MissionPortfolioTableProps {
  initialFilters?: Partial<MissionListFilters>;
  onMissionSelect?: (missionId: string) => void;
}

// ============================================================================
// Filter Components
// ============================================================================

interface FilterBarProps {
  filters: MissionListFilters;
  onFiltersChange: (filters: MissionListFilters) => void;
  totalCount: number;
}

function FilterBar({ filters, onFiltersChange, totalCount }: FilterBarProps) {
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const handleStatusChange = (value: string) => {
    setStatusFilter(value);
    onFiltersChange({
      ...filters,
      status: value === "all" ? undefined : (value as MissionStatus),
      page: 1,
    });
  };

  const handleTypeChange = (value: string) => {
    setTypeFilter(value);
    onFiltersChange({
      ...filters,
      mission_type: value === "all" ? undefined : (value as MissionType),
      page: 1,
    });
  };

  return (
    <div className="flex flex-wrap items-center gap-4 p-4 bg-white border-b rounded-t-lg">
      {/* Status Filter */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Status:</label>
        <select
          value={statusFilter}
          onChange={(e) => handleStatusChange(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="scheduled">Scheduled</option>
          <option value="draft">Draft</option>
        </select>
      </div>

      {/* Type Filter */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Type:</label>
        <select
          value={typeFilter}
          onChange={(e) => handleTypeChange(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="all">All</option>
          <option value="analysis">Analysis</option>
          <option value="planning">Planning</option>
          <option value="evaluation">Evaluation</option>
          <option value="design">Design</option>
          <option value="transformation">Transformation</option>
        </select>
      </div>

      {/* Results Count */}
      <div className="ml-auto text-sm text-gray-500">
        {totalCount} {totalCount === 1 ? "mission" : "missions"}
      </div>
    </div>
  );
}

// ============================================================================
// Status Badge Component
// ============================================================================

interface StatusBadgeProps {
  status: MissionStatus;
}

function StatusBadge({ status }: StatusBadgeProps) {
  const style = getStatusBadgeStyle(status);

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style.bgColor} ${style.textColor}`}
    >
      {style.label}
    </span>
  );
}

// ============================================================================
// Progress Bar Component
// ============================================================================

interface ProgressBarProps {
  completed: number;
  total: number;
}

function ProgressBar({ completed, total }: ProgressBarProps) {
  const percent = total > 0 ? (completed / total) * 100 : 0;

  const getBarColor = () => {
    if (percent >= 100) return "bg-green-500";
    if (percent >= 75) return "bg-blue-500";
    if (percent >= 50) return "bg-yellow-500";
    if (percent >= 25) return "bg-orange-500";
    return "bg-red-500";
  };

  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${getBarColor()} transition-all duration-300`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
      <span className="text-xs text-gray-600 min-w-[3rem]">
        {formatProgressCount(completed, total)}
      </span>
    </div>
  );
}

// ============================================================================
// Mission Row Component
// ============================================================================

interface MissionRowProps {
  mission: MissionListItem;
  onClick: () => void;
}

function MissionRow({ mission, onClick }: MissionRowProps) {
  return (
    <tr
      onClick={onClick}
      className="hover:bg-blue-50 cursor-pointer transition-colors border-b last:border-b-0"
    >
      {/* Title */}
      <td className="px-4 py-3">
        <div className="font-medium text-gray-900">{mission.title || "Untitled Mission"}</div>
        <div className="text-sm text-gray-500 truncate max-w-md" title={mission.objective}>
          {truncateText(mission.objective, 80)}
        </div>
      </td>

      {/* Status */}
      <td className="px-4 py-3">
        <StatusBadge status={mission.status} />
      </td>

      {/* Type */}
      <td className="px-4 py-3 text-sm text-gray-600">
        {formatMissionType(mission.mission_type)}
      </td>

      {/* Progress */}
      <td className="px-4 py-3">
        <ProgressBar
          completed={mission.progress.completed}
          total={mission.progress.total}
        />
      </td>

      {/* Updated */}
      <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
        <div title={formatDateTime(mission.updated_at)}>
          {formatRelativeTime(mission.updated_at)}
        </div>
      </td>
    </tr>
  );
}

// ============================================================================
// Loading State Component
// ============================================================================

function LoadingState() {
  return (
    <tbody>
      {[1, 2, 3, 4, 5].map((i) => (
        <tr key={i} className="border-b">
          <td className="px-4 py-3">
            <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
            <div className="h-3 bg-gray-200 rounded animate-pulse w-1/2 mt-2" />
          </td>
          <td className="px-4 py-3">
            <div className="h-6 bg-gray-200 rounded animate-pulse w-16" />
          </td>
          <td className="px-4 py-3">
            <div className="h-4 bg-gray-200 rounded animate-pulse w-20" />
          </td>
          <td className="px-4 py-3">
            <div className="h-2 bg-gray-200 rounded animate-pulse w-24" />
          </td>
          <td className="px-4 py-3">
            <div className="h-4 bg-gray-200 rounded animate-pulse w-16" />
          </td>
        </tr>
      ))}
    </tbody>
  );
}

// ============================================================================
// Empty State Component
// ============================================================================

interface EmptyStateProps {
  hasFilters: boolean;
  onClearFilters: () => void;
}

function EmptyState({ hasFilters, onClearFilters }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
        <svg
          className="w-8 h-8 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">No missions found</h3>
      <p className="text-sm text-gray-500 mb-4">
        {hasFilters
          ? "Try adjusting your filters to see more results."
          : "Get started by creating your first mission."}
      </p>
      {hasFilters && (
        <button
          onClick={onClearFilters}
          className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}

// ============================================================================
// Pagination Component
// ============================================================================

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalCount: number;
  perPage: number;
  onPageChange: (page: number) => void;
}

function Pagination({
  currentPage,
  totalPages,
  totalCount,
  perPage,
  onPageChange,
}: PaginationProps) {
  const startItem = (currentPage - 1) * perPage + 1;
  const endItem = Math.min(currentPage * perPage, totalCount);

  const pages: (number | string)[] = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i);
    }
  } else {
    pages.push(1);
    if (currentPage > 3) pages.push("...");
    for (
      let i = Math.max(2, currentPage - 1);
      i <= Math.min(totalPages - 1, currentPage + 1);
      i++
    ) {
      pages.push(i);
    }
    if (currentPage < totalPages - 2) pages.push("...");
    pages.push(totalPages);
  }

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-white border-t">
      <div className="text-sm text-gray-500">
        Showing {startItem} to {endItem} of {totalCount} missions
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        {pages.map((page, i) => (
          <button
            key={i}
            onClick={() => typeof page === "number" && onPageChange(page)}
            disabled={typeof page !== "number"}
            className={`px-3 py-1 text-sm border rounded ${
              page === currentPage
                ? "bg-blue-500 text-white border-blue-500"
                : "hover:bg-gray-50"
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {page}
          </button>
        ))}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function MissionPortfolioTable({
  initialFilters = {},
  onMissionSelect,
}: MissionPortfolioTableProps) {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<MissionListFilters>({
    page: 1,
    per_page: 20,
    sort_by: "updated_at",
    sort_order: "desc",
    ...initialFilters,
  });

  const { data, isLoading, isError, error, refetch } = useControlMissions(filters);

  const handleMissionClick = (missionId: string) => {
    if (onMissionSelect) {
      onMissionSelect(missionId);
    } else {
      navigate(`/control/missions/${missionId}`);
    }
  };

  const handlePageChange = (page: number) => {
    setFilters({ ...filters, page });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleClearFilters = () => {
    setFilters({
      page: 1,
      per_page: 20,
      sort_by: "updated_at",
      sort_order: "desc",
    });
  };

  const hasActiveFilters = !!filters.status || !!filters.mission_type;
  const totalPages = data ? Math.ceil(data.total / filters.per_page!) : 0;

  return (
    <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Mission Portfolio</h2>
        {isError && (
          <button
            onClick={() => refetch()}
            className="px-3 py-1 text-sm text-red-600 bg-red-50 rounded hover:bg-red-100"
          >
            Retry
          </button>
        )}
      </div>

      {/* Filters */}
      <FilterBar
        filters={filters}
        onFiltersChange={setFilters}
        totalCount={data?.total || 0}
      />

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Mission
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Progress
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Updated
              </th>
            </tr>
          </thead>

          {isLoading ? (
            <LoadingState />
          ) : isError ? (
            <tbody>
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-red-500">
                  {error instanceof Error ? error.message : "Failed to load missions"}
                </td>
              </tr>
            </tbody>
          ) : !data || data.missions.length === 0 ? (
            <tbody>
              <tr>
                <td colSpan={5}>
                  <EmptyState hasFilters={hasActiveFilters} onClearFilters={handleClearFilters} />
                </td>
              </tr>
            </tbody>
          ) : (
            <tbody>
              {data.missions.map((mission) => (
                <MissionRow
                  key={mission.id}
                  mission={mission}
                  onClick={() => handleMissionClick(mission.id)}
                />
              ))}
            </tbody>
          )}
        </table>
      </div>

      {/* Pagination */}
      {!isLoading && !isError && data && data.missions.length > 0 && (
        <Pagination
          currentPage={filters.page || 1}
          totalPages={totalPages}
          totalCount={data.total}
          perPage={filters.per_page || 20}
          onPageChange={handlePageChange}
        />
      )}
    </div>
  );
}
