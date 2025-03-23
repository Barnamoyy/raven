import { DataTable } from "@/components/data-table";
import SectionCard from "@/components/section-card";


import data from "./data.json";

import LatencyTimePlot from "@/components/charts/ltplot";

export default function Page() {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      <div className="grid auto-rows-min gap-4 md:grid-cols-4">
        <SectionCard
          title="Average Latency"
          value="4.5ms"
          percentage="+3.5%"
          status="Incrased over last 3 months"
          description="Total average latency less"
        />
        <SectionCard
          title="Min Delay"
          value="0.086ms"
          percentage="+0.21%"
          status="Incrased over last 3 months"
          description="Min delay increased by 0.21%"
        />
        <SectionCard
          title="Max Delay"
          value="2.581ms"
          percentage="+2.1%"
          status="Incrased over last 3 months"
          description="Max delay decreased by 2.1%"
        />
        <SectionCard
          title="Jitter"
          value="4.5ms"
          percentage="+3.5%"
          status="Incrased over last 3 months"
          description="Total average latency less"
        />
      </div>
      <div className="bg-muted/50 min-h-[100vh] flex-1 rounded-xl md:min-h-min">
      <LatencyTimePlot />
      </div>
      <DataTable data={data} />
    </div>
  );
}
