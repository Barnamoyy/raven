"use client";

import DelayAnalysis from "@/components/charts/delaychart";
import ProtocolDistributionChart from "@/components/charts/ProtocolDistributionChart";

import { useDataStore } from "@/store/useDataStore";

const Page = () => {
  const { latest } = useDataStore();
  const analysis = latest;
  const distribution =
    latest?.analysis_results?.pattern_analysis?.protocol_distribution;
  console.log(distribution);

  return (
    <div className="flex flex-col w-screen justify-center items-center">
      {/* <div className="grid grid-cols-4 gap-4 w-full hl-full">

      <div className="bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="bg-muted/50 col-span-2 p-4 rounded-xl min-h-[150px]"></div>
      <div className="bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="col-span-2 bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="col-span-1 bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="col-span-1 bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="col-span-2 bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="col-span-2 bg-muted/50 p-4 rounded-xl min-h-[150px]"></div> */}
      <DelayAnalysis responseData={analysis} />
      <ProtocolDistributionChart data={distribution} />
    </div>
  );
};

export default Page;
