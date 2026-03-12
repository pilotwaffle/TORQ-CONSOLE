/**
 * Phase 3: Product UX & Identity
 *
 * Consistent Page Header Component
 * Provides uniform page headers with CTAs across all pages
 */

import { Plus, RefreshCw, Settings, HelpCircle, MoreHorizontal } from 'lucide-react';
import { useState } from 'react';

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  breadcrumbs?: Array<{ label: string; href?: string }>;
  primaryAction?: {
    label: string;
    icon?: React.ReactNode;
    onClick: () => void;
    href?: string;
    disabled?: boolean;
  };
  secondaryActions?: Array<{
    label: string;
    icon?: React.ReactNode;
    onClick: () => void;
    href?: string;
  }>;
  meta?: React.ReactNode;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export function PageHeader({
  title,
  description,
  actions,
  breadcrumbs,
  primaryAction,
  secondaryActions,
  meta,
  onRefresh,
  isLoading,
}: PageHeaderProps) {
  const [showMoreMenu, setShowMoreMenu] = useState(false);

  return (
    <div className="border-b border-gray-200 bg-white">
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <div className="px-6 pt-4 pb-2">
          <nav className="flex items-center gap-2 text-sm">
            {breadcrumbs.map((crumb, i) => (
              <div key={i} className="flex items-center gap-2">
                {i > 0 && (
                  <span className="text-gray-300">/</span>
                )}
                {crumb.href ? (
                  <a
                    href={crumb.href}
                    className="text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    {crumb.label}
                  </a>
                ) : (
                  <span className="text-gray-900 font-medium">{crumb.label}</span>
                )}
              </div>
            ))}
          </nav>
        </div>
      )}

      {/* Main Header */}
      <div className="px-6 py-4">
        <div className="flex items-start justify-between gap-4">
          {/* Left: Title and description */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
              {isLoading && (
                <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              )}
            </div>
            {description && (
              <p className="text-sm text-gray-500 mt-1">{description}</p>
            )}
            {meta && (
              <div className="mt-2">{meta}</div>
            )}
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-3">
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isLoading}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                title="Refresh"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            )}

            {secondaryActions && secondaryActions.length > 0 && (
              <div className="flex items-center gap-2">
                {secondaryActions.slice(0, 2).map((action, i) => (
                  action.href ? (
                    <a
                      key={i}
                      href={action.href}
                      className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      {action.icon && <span className="w-4 h-4 mr-2">{action.icon}</span>}
                      {action.label}
                    </a>
                  ) : (
                    <button
                      key={i}
                      onClick={action.onClick}
                      className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      {action.icon && <span className="w-4 h-4 mr-2">{action.icon}</span>}
                      {action.label}
                    </button>
                  )
                ))}
                {secondaryActions.length > 2 && (
                  <div className="relative">
                    <button
                      onClick={() => setShowMoreMenu(!showMoreMenu)}
                      className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <MoreHorizontal className="w-4 h-4" />
                    </button>
                    {showMoreMenu && (
                      <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[200px]">
                        {secondaryActions.slice(2).map((action, i) => (
                          <button
                            key={i}
                            onClick={() => {
                              action.onClick();
                              setShowMoreMenu(false);
                            }}
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                          >
                            {action.icon && <span className="w-4 h-4">{action.icon}</span>}
                            {action.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {primaryAction && (
              primaryAction.href ? (
                <a
                  href={primaryAction.href}
                  className={`inline-flex items-center px-4 py-2 rounded-lg font-medium transition-colors shadow-sm hover:shadow-md ${
                    primaryAction.disabled
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {primaryAction.icon && <span className="w-4 h-4 mr-2">{primaryAction.icon}</span>}
                  {primaryAction.label}
                </a>
              ) : (
                <button
                  onClick={primaryAction.onClick}
                  disabled={primaryAction.disabled}
                  className={`inline-flex items-center px-4 py-2 rounded-lg font-medium transition-colors shadow-sm hover:shadow-md ${
                    primaryAction.disabled
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {primaryAction.icon && <span className="w-4 h-4 mr-2">{primaryAction.icon}</span>}
                  {primaryAction.label}
                </button>
              )
            )}

            {actions}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Simplified Page Header for pages without complex actions
 */
interface SimplePageHeaderProps {
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
  rightContent?: React.ReactNode;
}

export function SimplePageHeader({ title, description, action, rightContent }: SimplePageHeaderProps) {
  return (
    <div className="border-b border-gray-200 bg-white px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
          {description && (
            <p className="text-sm text-gray-500 mt-1">{description}</p>
          )}
        </div>
        {(action || rightContent) && (
          <div className="flex items-center gap-3">
            {action && (
              <button
                onClick={action.onClick}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                {action.icon && <span className="w-4 h-4 mr-2">{action.icon}</span>}
                {action.label}
              </button>
            )}
            {rightContent}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Compact page header for nested pages
 */
interface CompactPageHeaderProps {
  title: string;
  backButton?: {
    label: string;
    onClick: () => void;
  };
  actions?: React.ReactNode;
}

export function CompactPageHeader({ title, backButton, actions }: CompactPageHeaderProps) {
  return (
    <div className="border-b border-gray-200 bg-white px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {backButton && (
            <button
              onClick={backButton.onClick}
              className="text-gray-500 hover:text-gray-700 flex items-center gap-1 text-sm"
            >
              ← {backButton.label}
            </button>
          )}
          <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
        </div>
        {actions}
      </div>
    </div>
  );
}
