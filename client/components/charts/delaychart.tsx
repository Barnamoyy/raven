import React, { useEffect, useState } from "react";
import { Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
} from "chart.js";

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement
);

interface DelayAnalysisProps {
  responseData: any;
}

const DelayAnalysis: React.FC<DelayAnalysisProps> = ({ responseData }) => {
  const [pieData, setPieData] = useState<any>({});
  const [setBarData] = useState<any>({});

  useEffect(() => {
    // Ensure responseData exists and contains delay categorization information
    if (!responseData?.analysis_results?.delay_categorization) return;

    const delayCat = responseData.analysis_results.delay_categorization;
    const delayCategories = delayCat.summary?.delay_categories || {};
    const delayStats = delayCat.delays || {};

    // Prepare pie chart data using delay categories
    const pieLabels = Object.keys(delayCategories);
    const pieValues = Object.values(delayCategories);
    setPieData({
      labels: pieLabels,
      datasets: [
        {
          label: "Delay Categories",
          data: pieValues,
          backgroundColor: [
            "#4CAF50", // Green
            "#FFC107", // Amber
            "#FF5722", // Deep Orange
            "#03A9F4", // Light Blue
            "#9C27B0", // Purple
          ],
          borderColor: ["#388E3C", "#FFA000", "#E64A19", "#0288D1", "#7B1FA2"],
          borderWidth: 1,
        },
      ],
    });

    // Prepare bar chart data using delay statistics
    const barLabels = Object.keys(delayStats);
    const barValues = Object.values(delayStats);
    setBarData({
      labels: barLabels,
      datasets: [
        {
          label: "Delay Statistics (seconds)",
          data: barValues,
          backgroundColor: "#3F51B5",
        },
      ],
    });
  }, [responseData]);

  return (
    <div className="align-middle w-full bg-gray-50 flex flex-col items-center p-8">
      <div className="grid  grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-6xl">
        <div className="bg-white rounded-lg shadow-lg p-6  flex  flex-col justify-center items-center w-full">
          <h2 className="text-2xl font-semibold mb-4 text-center">
            Delay Categories
          </h2>
          {pieData?.labels && (
            <div className="relative mx-auto justify-center items-center   h-72">
              <Pie data={pieData} options={{ maintainAspectRatio: false }} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DelayAnalysis;
