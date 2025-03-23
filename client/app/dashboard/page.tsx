"use client";

import SectionCard from "@/components/section-card";

import { useDataStore } from "@/store/useDataStore";

import { PacketDataTable } from "@/components/table.tsx/packet-data-table";
import Dashboard from "@/components/charts/ltchart";

export default function Page() {
  const { latest } = useDataStore();

  const analysis_data = latest;

  const summary =
    analysis_data?.analysis_results?.delay_categorization?.summary;
  const table_data =
    analysis_data?.analysis_results?.congestion_analysis?.packet_flow;
  console.log(analysis_data);

  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      <div className="grid auto-rows-min gap-4 md:grid-cols-4">
        <SectionCard
          title="Average Latency"
          value={`${(summary?.delays?.average * 1000).toFixed(2)}ms`}
          status={`Max Latency: ${(summary?.delays?.max * 1000).toFixed(2)}ms`}
          description={`median Latency: ${(
            summary?.delays?.median * 1000
          ).toFixed(2)}ms`}
        />
        <SectionCard
          title="Packet Count"
          value={`${summary?.packet_count}`}
          status={`Mqtt Packets: ${summary?.mqtt_traffic?.packets}`}
          description={`Mqtt Packets: ${summary?.mqtt_traffic?.percentage?.toFixed(
            2
          )}`}
        />
        <SectionCard
          title="Congestion Events"
          value={`${summary?.delay_categories?.network_congestion_events}`}
          status={`Bundling Delays: ${summary?.delay_categories?.bundling_delays}`}
          description={`Bundling Delays: ${summary?.delay_categories?.retransmission_delays}`}
        />
        <SectionCard
          title="Protocol Count"
          value={`${Object.keys(summary?.protocols || {}).length}`}
          status={`IPv4: ${summary?.protocols[6]}`}
          description={`IPv6: ${summary?.protocols[17]}`}
        />
      </div>

      {/* Interactive Charts Dashboard */}
      <div className="bg-muted/50 min-h-auto flex-1 rounded-xl p-4">
        {/* The Dashboard component shows several interactive charts based on the analysis results */}
        {analysis_data?.analysis_results && (
          <Dashboard analysisResults={analysis_data.analysis_results} />
        )}
      </div>
      {table_data && (
        <div className="bg-muted/50 rounded-xl p-4">
          <PacketDataTable data={table_data} />
        </div>
      )}
      <div className="bg-muted/50 min-h-[100vh] flex-1 rounded-xl md:min-h-min"></div>
    </div>
  );
}
