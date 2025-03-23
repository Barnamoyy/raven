"use client";

import React from "react";
import DelayChart, { RootCauseAnalysis } from "@/components/charts/rootcause";
import { useDataStore } from "@/store/useDataStore";

const categories: Array<keyof RootCauseAnalysis> = [
  "by_size",
  "by_protocol",
  "by_source",
  "by_destination",
  "by_port",
];

const Page = () => {
  const { latest } = useDataStore();
  const root_cause_analysis =
    latest?.analysis_results?.mqtt_analysis?.root_cause_analysis;

  return (
    // Outer container: centers content and provides horizontal + vertical padding
    <div className="w-full  px-4 py-8 space-y-8">
      {categories.map((category) => (
        <div key={category} className="w-full">
          <DelayChart data={{ root_cause_analysis }} category={category} />
        </div>
      ))}
    </div>
  );
};

export default Page;
