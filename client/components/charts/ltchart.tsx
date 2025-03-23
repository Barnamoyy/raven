"use client";

import React from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui/tabs';

import { Doughnut, Pie, Line } from 'react-chartjs-2';
import {
  Chart,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
} from 'chart.js';

// Register Chart.js components
Chart.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title
);

interface AnalysisResults {
  avg_latency: number;
  congestion_analysis: {
    congestion_score: number;
    congestion_level: string;
    packet_flow: Array<{
      timestamp?: string;
      latency?: number;
    }>;
  };
  delay_categorization: {
    summary: { [key: string]: number };
  };
  mqtt_analysis: {
    packet_count: number;
    protocol_distribution: { [key: string]: number };
    flows: number;
  };
  pattern_analysis: {
    statistics: any;
    protocol_distribution: any;
  };
  tcp_window_analysis: {
    window_size_analysis: any;
    zero_window_events: any[];
    window_scale_factors: any;
    congestion_indicators: any;
  };
}

interface DashboardProps {
  analysisResults: AnalysisResults;
}

const Dashboard: React.FC<DashboardProps> = ({ analysisResults }) => {
  // -------------------------------
  // 1. Congestion Analysis Chart (Doughnut)
  // -------------------------------
  const congestionData = {
    labels: ['Congestion Score', 'Remaining'],
    datasets: [
      {
        data: [
          analysisResults.congestion_analysis.congestion_score,
          100 - analysisResults.congestion_analysis.congestion_score,
        ],
        backgroundColor: ['#34D399', '#D1D5DB'],
      },
    ],
  };

  // -------------------------------
  // 2. Delay Categorization Chart (Doughnut)
  // -------------------------------
  const delayLabels = Object.keys(
    analysisResults.delay_categorization.summary
  );
  const delayValues = Object.values(
    analysisResults.delay_categorization.summary
  );
  const delayData = {
    labels: delayLabels,
    datasets: [
      {
        data: delayValues,
        backgroundColor: ['#F87171', '#FBBF24', '#34D399', '#60A5FA'],
      },
    ],
  };

  // -------------------------------
  // 3. Protocol Distribution Chart (Pie Chart)
  // -------------------------------
  const protocolLabels = Object.keys(
    analysisResults.mqtt_analysis.protocol_distribution
  );
  const protocolValues = Object.values(
    analysisResults.mqtt_analysis.protocol_distribution
  );
  const protocolData = {
    labels: protocolLabels,
    datasets: [
      {
        data: protocolValues,
        backgroundColor: ['#60A5FA', '#FBBF24', '#F87171', '#34D399', '#A78BFA'],
      },
    ],
  };

  // -------------------------------
  // 4. Latency Trend Chart (Line Chart) for All Packets
  // -------------------------------
  const packetFlow = analysisResults.congestion_analysis.packet_flow || [];
  
  const latencyTrendLabels = packetFlow.map((packet, index) =>
    packet.timestamp ? new Date(packet.timestamp).toLocaleTimeString() : `Packet ${index + 1}`
  );

  const latencyTrendValues = packetFlow.map(packet =>
    packet.latency ?? analysisResults.avg_latency
  );

  const latencyTrendData = {
    labels: latencyTrendLabels,
    datasets: [
      {
        label: 'Latency (s)',
        data: latencyTrendValues,
        borderColor: '#34D399',
        fill: false,
        tension: 0.4, // Increased tension for a more curved line
      },
    ],
  };

  // Chart options: disable aspect ratio so container size controls dimensions
  const chartOptions = {
    maintainAspectRatio: false,
    responsive: true,
  };

  // Container style for reduced chart size
  const chartContainerStyle: React.CSSProperties = {
    height: '300px',
    width: '100%',
    position: 'relative',
  };

  return (
    <div className="p-4 space-y-6">
      <Tabs defaultValue="congestion" className="w-full">
        <TabsList>
          <TabsTrigger value="congestion">Congestion</TabsTrigger>
          <TabsTrigger value="delay">Delay Categorization</TabsTrigger>
          <TabsTrigger value="protocol">Protocol Distribution</TabsTrigger>
          <TabsTrigger value="latency">Latency Trend</TabsTrigger>
        </TabsList>

        {/* Congestion Analysis Tab */}
        <TabsContent value="congestion">
          <Card>
            <CardHeader>
              <CardTitle>Congestion Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div style={chartContainerStyle}>
                <Doughnut data={congestionData} options={chartOptions} />
              </div>
              <p className="mt-2">
                Congestion Level: <strong>{analysisResults.congestion_analysis.congestion_level}</strong>
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Delay Categorization Tab */}
        <TabsContent value="delay">
          <Card>
            <CardHeader>
              <CardTitle>Delay Categorization</CardTitle>
            </CardHeader>
            <CardContent>
              <div style={chartContainerStyle}>
                <Doughnut data={delayData} options={chartOptions} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Protocol Distribution Tab */}
        <TabsContent value="protocol">
          <Card>
            <CardHeader>
              <CardTitle>Protocol Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div style={chartContainerStyle}>
                <Pie data={protocolData} options={chartOptions} />
              </div>
              <p className="mt-2">
                Total Packet Count: <strong>{analysisResults.mqtt_analysis.packet_count}</strong>
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Latency Trend Tab */}
        <TabsContent value="latency">
          <Card>
            <CardHeader>
              <CardTitle>Latency Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <div style={chartContainerStyle}>
                <Line data={latencyTrendData} options={chartOptions} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard;
