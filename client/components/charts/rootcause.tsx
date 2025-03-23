"use client";

import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from "chart.js";
import { Line } from "react-chartjs-2";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  LogarithmicScale, // for optional log scale
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

type DelayData = {
  avg_delay: number;
  min_delay: number;
  max_delay: number;
  count: number;
  std_dev: number;
};

export type RootCauseAnalysis = {
  by_size: Record<string, DelayData>;
  by_protocol: Record<string, DelayData>;
  by_source: Record<string, DelayData>;
  by_destination: Record<string, DelayData>;
  by_port: Record<string, DelayData>;
};

interface DelayChartProps {
  data: {
    root_cause_analysis: RootCauseAnalysis | null;
  };
  category: keyof RootCauseAnalysis; // e.g. "by_size", "by_protocol", etc.
}

export default function DelayChart({ data, category }: DelayChartProps) {
  // Guard: Return early if no data is available
  if (!data.root_cause_analysis) {
    return <div>No data available</div>;
  }

  // Extract the data for the selected category:
  const categoryData = data.root_cause_analysis[category];
  const labels = Object.keys(categoryData);

  // Prepare dataset arrays:
  const avgDelays = labels.map((key) => categoryData[key].avg_delay);
  const minDelays = labels.map((key) => categoryData[key].min_delay);
  const maxDelays = labels.map((key) => categoryData[key].max_delay);
  const counts = labels.map((key) => categoryData[key].count);

  // Build chart data
  const chartData = {
    labels,
    datasets: [
      {
        label: "Average Delay",
        data: avgDelays,
        borderColor: "#3b82f6", // Tailwind blue-500
        backgroundColor: "rgba(59, 130, 246, 0.2)",
        tension: 0.4,
      },
      {
        label: "Min Delay",
        data: minDelays,
        borderColor: "#ef4444", // Tailwind red-500
        backgroundColor: "rgba(239, 68, 68, 0.2)",
        tension: 0.4,
      },
      {
        label: "Max Delay",
        data: maxDelays,
        borderColor: "#10b981", // Tailwind green-500
        backgroundColor: "rgba(16, 185, 129, 0.2)",
        tension: 0.4,
      },
      {
        label: "Count",
        data: counts,
        borderColor: "#a855f7", // Tailwind purple-500
        backgroundColor: "rgba(168, 85, 247, 0.2)",
        tension: 0.4,
        yAxisID: "y1",
      },
    ],
  };

  // Configure Chart.js options
  const options: ChartOptions<"line"> = {
    responsive: true,
    // Allows the chart to fill the container rather than maintain an aspect ratio
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    scales: {
      x: {
        // If you have too many or lengthy labels, consider skipping or rotating them
        ticks: {
          autoSkip: false,
          maxRotation: 45,
          minRotation: 0,
          // For many labels, you could enable skipping:
          // autoSkip: true,
          // maxTicksLimit: 10,
        },
      },
      // For linear scale:
      y: {
        type: "linear",
        display: true,
        position: "left",
        // You can optionally control the range:
        // suggestedMin: 0,
        // suggestedMax: 100,
      },
      // If you want a log scale, swap "type" to "logarithmic":
      // y: {
      //   type: "logarithmic",
      //   display: true,
      //   position: "left",
      //   ticks: {
      //     callback: function (value) {
      //       return Number(value).toLocaleString();
      //     },
      //   },
      // },
      y1: {
        type: "linear",
        display: true,
        position: "right",
        grid: {
          drawOnChartArea: false,
        },
      },
    },
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: `Delay Analysis by ${category.replace("by_", "")}`,
      },
    },
  };

  return (
    // The container with controlled height/width via Tailwind
    <div className="p-4 bg-white rounded shadow h-[400px] w-full  mx-auto my-4">
      <Line data={chartData} options={options} />
    </div>
  );
}
