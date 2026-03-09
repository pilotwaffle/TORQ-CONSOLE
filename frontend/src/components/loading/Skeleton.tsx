/**
 * Phase 3: Product UX & Identity
 *
 * Skeleton Loading Components
 * Provides visual placeholders during content loading
 */

/**
 * Table Skeleton
 */
export function TableSkeleton({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex gap-4 mb-4">
        {Array.from({ length: columns }).map((_, i) => (
          <div key={i} className="h-4 bg-gray-200 rounded w-24 animate-pulse" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 py-3 border-b border-gray-100">
          {Array.from({ length: columns }).map((_, j) => (
            <div key={j} className="h-4 bg-gray-200 rounded flex-1 animate-pulse" style={{ animationDelay: `${j * 100}ms` }} />
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * Card Grid Skeleton
 */
export function CardGridSkeleton({ cards = 4 }: { cards?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {Array.from({ length: cards }).map((_, i) => (
        <div key={i} className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse" />
          <div className="h-3 bg-gray-200 rounded w-1/2 animate-pulse" />
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded animate-pulse" />
            <div className="h-3 bg-gray-200 rounded w-5/6 animate-pulse" />
          </div>
          <div className="flex gap-2">
            <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
            <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Workflow Card Skeleton
 */
export function WorkflowCardSkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-start justify-between mb-4">
        <div className="space-y-2 flex-1">
          <div className="h-5 bg-gray-200 rounded w-1/2 animate-pulse" />
          <div className="h-3 bg-gray-200 rounded w-1/3 animate-pulse" />
        </div>
        <div className="h-8 w-8 bg-gray-200 rounded animate-pulse" />
      </div>
      <div className="space-y-2 mb-4">
        <div className="h-3 bg-gray-200 rounded animate-pulse" />
        <div className="h-3 bg-gray-200 rounded w-2/3 animate-pulse" />
      </div>
      <div className="flex items-center gap-4 text-sm text-gray-500">
        <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
      </div>
    </div>
  );
}

/**
 * Timeline Skeleton
 */
export function TimelineSkeleton({ items = 3 }: { items?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div className="w-3 h-3 bg-gray-300 rounded-full" />
            {i < items - 1 && <div className="w-0.5 h-16 bg-gray-200" />}
          </div>
          <div className="flex-1 p-4 bg-gray-50 rounded-lg">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-2 animate-pulse" />
            <div className="h-3 bg-gray-200 rounded w-full animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Chat Message Skeleton
 */
export function ChatMessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {!isUser && (
        <div className="w-8 h-8 bg-gray-200 rounded-full flex-shrink-0 animate-pulse" />
      )}
      <div className={`max-w-2xl ${isUser ? 'bg-blue-600' : 'bg-gray-100'} rounded-2xl px-4 py-3`}>
        <div className={`h-4 rounded mb-2 animate-pulse ${isUser ? 'bg-blue-500 w-32' : 'bg-gray-300 w-48'}`} />
        <div className={`h-4 rounded animate-pulse ${isUser ? 'bg-blue-500 w-64' : 'bg-gray-300 w-full'}`} />
      </div>
      {isUser && (
        <div className="w-8 h-8 bg-gray-200 rounded-full flex-shrink-0 animate-pulse" />
      )}
    </div>
  );
}

/**
 * Page Header Skeleton
 */
export function PageHeaderSkeleton() {
  return (
    <div className="border-b border-gray-200 bg-white px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-6 bg-gray-200 rounded w-48 animate-pulse" />
          <div className="h-4 bg-gray-200 rounded w-64 animate-pulse" />
        </div>
        <div className="h-9 w-32 bg-gray-200 rounded-lg animate-pulse" />
      </div>
    </div>
  );
}

/**
 * Stats Row Skeleton
 */
export function StatsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-white border border-gray-200 rounded-xl p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="h-4 bg-gray-200 rounded w-20 animate-pulse" />
            <div className="h-8 w-8 bg-gray-200 rounded-full animate-pulse" />
          </div>
          <div className="h-8 bg-gray-200 rounded w-16 animate-pulse" />
          <div className="h-3 bg-gray-200 rounded w-full mt-2 animate-pulse" />
        </div>
      ))}
    </div>
  );
}
