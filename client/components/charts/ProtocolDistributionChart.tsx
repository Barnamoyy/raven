"use client";

import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartData,
} from "chart.js";
import { Bar } from "react-chartjs-2";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export interface ProtocolDistributionData {
  count: number;
  bytes: number;
  total_delay: number;
  avg_latency: number;
  min_latency: number;
  max_latency: number;
  median_latency: number;
  std_latency: number;
}

interface ProtocolDistributionChartProps {
  data: Record<string, ProtocolDistributionData>;
}

export default function ProtocolDistributionChart({
  data,
}: ProtocolDistributionChartProps) {
  if (!data) {
    return <div>No data available</div>;
  }
  console.log(data);
  // Extract protocol names
  const protocols = Object?.keys(data);

  // Build arrays for each metric (excluding 'count' and 'bytes')
  const totalDelays = protocols.map((p) => data[p].total_delay);
  const avgLatencies = protocols.map((p) => data[p].avg_latency);
  const minLatencies = protocols.map((p) => data[p].min_latency);
  const maxLatencies = protocols.map((p) => data[p].max_latency);
  const medianLatencies = protocols.map((p) => data[p].median_latency);
  const stdLatencies = protocols.map((p) => data[p].std_latency);

  // Build chart data:
  // - total_delay goes on left axis (y)
  // - all other latency metrics go on right axis (y1)
  const chartData: ChartData<"bar"> = {
    labels: protocols,
    datasets: [
      {
        label: "Total Delay (s)",
        data: totalDelays,
        backgroundColor: "rgba(75, 192, 192, 0.6)",
        yAxisID: "y", // Left axis
      },
      {
        label: "Avg Latency (s)",
        data: avgLatencies,
        backgroundColor: "rgba(255, 99, 132, 0.6)",
        yAxisID: "y1", // Right axis
      },
      {
        label: "Min Latency (s)",
        data: minLatencies,
        backgroundColor: "rgba(255, 159, 64, 0.6)",
        yAxisID: "y1",
      },
      {
        label: "Max Latency (s)",
        data: maxLatencies,
        backgroundColor: "rgba(153, 102, 255, 0.6)",
        yAxisID: "y1",
      },
      {
        label: "Median Latency (s)",
        data: medianLatencies,
        backgroundColor: "rgba(54, 162, 235, 0.6)",
        yAxisID: "y1",
      },
      {
        label: "Std Latency (s)",
        data: stdLatencies,
        backgroundColor: "rgba(255, 205, 86, 0.6)",
        yAxisID: "y1",
      },
    ],
  };

  // Configure chart options
  const options: ChartOptions<"bar"> = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: {
          autoSkip: false,
          maxRotation: 45,
          minRotation: 0,
        },
      },
      y: {
        type: "linear",
        position: "left",
        title: {
          display: true,
          text: "Total Delay (s)",
        },
      },
      y1: {
        type: "linear",
        position: "right",
        grid: {
          drawOnChartArea: false, // Prevent grid lines from y1 overlapping with y
        },
        title: {
          display: true,
          text: "Latency (s)",
        },
      },
    },
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: "Protocol Delay Distribution",
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            const label = context.dataset.label || "";
            const value = context.parsed.y;
            // Show up to 5 decimal places
            return `${label}: ${value.toFixed(5)} s`;
          },
        },
      },
    },
  };

  return (
    <div className="p-4 bg-white rounded shadow h-[500px] w-full max-w-5xl mx-auto my-4">
      <Bar data={chartData} options={options} />
    </div>
  );
}
