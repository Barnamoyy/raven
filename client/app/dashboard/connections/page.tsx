"use client";

import React, { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  Node,
  Edge,
  Handle,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { useDataStore } from "@/store/useDataStore";

// -----------------------------------------------------------------
// Custom Node Component: StarNode (ignores the id prop)
// -----------------------------------------------------------------
const StarNode = ({ data }: { data: any }) => {
  return (
    <div
      style={{
        width: 80,
        height: 80,
        borderRadius: "50%",
        backgroundColor: "#fff",
        border: "2px solid #34D399",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        cursor: "grab",
        boxShadow: "0px 2px 6px rgba(0, 0, 0, 0.1)",
        textAlign: "center",
        fontSize: "12px",
      }}
    >
      {data.label}
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: "#555", width: 10, height: 10 }}
      />
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: "#555", width: 10, height: 10 }}
      />
    </div>
  );
};

const nodeTypes = { starNode: StarNode };

export default function Page() {
  const { latest } = useDataStore();

  // Always call hooks in the same order.
  const analysis =
    latest?.analysis_results?.congestion_analysis?.packet_flow || [];

  const packetFlow = useMemo(() => {
    return analysis
      .map((item: any) => ({
        source_ip: item.src_ip,
        destination_ip: item.dst_ip,
      }))
      .filter((packet: any) => packet.source_ip !== packet.destination_ip);
  }, [analysis]);

  // Compute unique nodes and determine center node.
  const { nodesArray, centerNodeId } = useMemo(() => {
    const nodeMap = new Map<string, Node>();
    const outDegree = new Map<string, number>();

    packetFlow.forEach((packet: any) => {
      outDegree.set(
        packet.source_ip,
        (outDegree.get(packet.source_ip) || 0) + 1
      );

      if (!nodeMap.has(packet.source_ip)) {
        nodeMap.set(packet.source_ip, {
          id: packet.source_ip,
          data: { label: packet.source_ip },
          position: { x: 0, y: 0 },
        });
      }

      if (!nodeMap.has(packet.destination_ip)) {
        nodeMap.set(packet.destination_ip, {
          id: packet.destination_ip,
          data: { label: packet.destination_ip },
          position: { x: 0, y: 0 },
        });
      }
    });

    let maxDegree = -1;
    let centerId: string | undefined = undefined;
    outDegree.forEach((degree, ip) => {
      if (degree > maxDegree) {
        maxDegree = degree;
        centerId = ip;
      }
    });

    if (!centerId) {
      centerId = nodeMap.keys().next().value;
    }

    return {
      nodesArray: Array.from(nodeMap.values()),
      centerNodeId: centerId as string,
    };
  }, [packetFlow]);

  // Arrange nodes in a star layout.
  const positionedNodes = useMemo((): Node[] => {
    const centerX = 400;
    const centerY = 300;
    const radius = 200;
    const updatedNodes = nodesArray.map((n) => ({ ...n }));

    updatedNodes.forEach((node) => {
      if (node.id === centerNodeId) {
        node.position = { x: centerX - 40, y: centerY - 40 };
      }
    });

    const otherNodes = updatedNodes.filter((n) => n.id !== centerNodeId);
    const count = otherNodes.length;
    otherNodes.forEach((node, index) => {
      const angle = (2 * Math.PI * index) / count;
      node.position = {
        x: centerX + radius * Math.cos(angle) - 40,
        y: centerY + radius * Math.sin(angle) - 40,
      };
    });

    return updatedNodes.map((node) => ({
      ...node,
      type: "starNode",
    }));
  }, [nodesArray, centerNodeId]);

  // Create edges based on packetFlow.
  const edges = useMemo<Edge[]>(() => {
    return packetFlow.map((packet: any, idx: number) => ({
      id: `e-${packet.source_ip}-${packet.destination_ip}-${idx}`,
      source: packet.source_ip,
      target: packet.destination_ip,
      animated: true,
      type: "smoothstep",
    }));
  }, [packetFlow]);

  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <h1 className="text-3xl font-semibold text-center my-4">
        IPv4 Connections
      </h1>
      {packetFlow.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <h2 className="text-xl font-semibold">No data available</h2>
        </div>
      ) : (
        <ReactFlow
          nodes={positionedNodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background color="#aaa" gap={16} />
          <Controls />
        </ReactFlow>
      )}
    </div>
  );
}
