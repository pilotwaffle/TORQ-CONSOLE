/**
 * Operator Control Surface - Main Control Page
 *
 * Landing page for the Operator Control Surface showing the
 * Mission Portfolio Panel as the entry point to all mission views.
 */

import { MissionPortfolioTable } from "../components/MissionPortfolioTable";

export default function ControlPage() {
  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Operator Control Surface</h1>
        <p className="text-gray-500 mt-1">
          Mission command center with real-time visibility into mission execution.
        </p>
      </div>

      {/* Mission Portfolio Table */}
      <MissionPortfolioTable />
    </div>
  );
}
