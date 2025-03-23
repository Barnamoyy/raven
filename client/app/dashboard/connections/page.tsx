"use client";

import React, { useMemo, useCallback } from "react";
import ReactFlow, {
  Background,
  Controls,
  addEdge,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  Handle,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { motion } from "framer-motion";

import { useDataStore } from "@/store/useDataStore";

// -----------------------------------------------------------------
// Sample packet data; replace this with your actual analysis data
// -----------------------------------------------------------------

// -----------------------------------------------------------------
// Custom Node Component: StarNode
// A round node with a floating IP label and connection handles
// -----------------------------------------------------------------
const StarNode = ({ id, data }: { id: string; data: any }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
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
      {/* Connection Handles */}
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
    </motion.div>
  );
};

// Register our custom node type
const nodeTypes = {
  starNode: StarNode,
};

// -----------------------------------------------------------------
// Main Page Component
// -----------------------------------------------------------------
export default function Page() {
  const { latest } = useDataStore();

  const analysis = latest?.analysis_results?.congestion_analysis?.packet_flow;

  const packetFlow = analysis
  ?.map((item: any) => ({
    source_ip: item.src_ip,
    destination_ip: item.dst_ip,
  }))
  .filter((packet:any) => packet.source_ip !== packet.destination_ip);

  console.log(packetFlow)

  // -----------------------------------------------------------------
  // 1. Compute unique nodes and record out-degree for each source IP
  // Provide a default position to satisfy Node type requirements.
  // -----------------------------------------------------------------

  const { nodesArray, centerNodeId } = useMemo(() => {
    const nodeMap = new Map<string, Node>();
    const outDegree = new Map<string, number>();

    packetFlow?.forEach((packet: any) => {
      // Increase out-degree for source IP
      outDegree.set(
        packet.source_ip,
        (outDegree.get(packet.source_ip) || 0) + 1
      );

      // Add source IP node if it doesn't exist
      if (!nodeMap.has(packet.source_ip)) {
        nodeMap.set(packet.source_ip, {
          id: packet.source_ip,
          data: { label: packet.source_ip },
          position: { x: 0, y: 0 },
        });
      }

      // Add destination IP node if it doesn't exist
      if (!nodeMap.has(packet.destination_ip)) {
        nodeMap.set(packet.destination_ip, {
          id: packet.destination_ip,
          data: { label: packet.destination_ip },
          position: { x: 0, y: 0 },
        });
      }
    });

    // Determine the central node (node with highest out-degree)
    let maxDegree = -1;
    let centerId: string | undefined = undefined;
    outDegree.forEach((degree, ip) => {
      if (degree > maxDegree) {
        maxDegree = degree;
        centerId = ip;
      }
    });

    // Fallback: if no center found, use the first node from the map
    if (!centerId) {
      centerId = nodeMap.keys().next().value;
    }

    return {
      nodesArray: Array.from(nodeMap.values()),
      centerNodeId: centerId as string,
    };
  }, []);

  // -----------------------------------------------------------------
  // 2. Arrange nodes in a star layout
  // Central node is positioned at the canvas center,
  // and all other nodes are distributed evenly in a circle.
  // -----------------------------------------------------------------
  const positionedNodes = useMemo((): Node[] => {
    const centerX = 400;
    const centerY = 300;
    const radius = 200;

    // Create a copy of the nodesArray
    const updatedNodes = nodesArray.map((node) => ({ ...node }));

    // Position the central node at the center of the canvas
    updatedNodes.forEach((node) => {
      if (node.id === centerNodeId) {
        node.position = { x: centerX - 40, y: centerY - 40 };
      }
    });

    // Distribute peripheral nodes evenly around the central node
    const otherNodes = updatedNodes.filter((node) => node.id !== centerNodeId);
    const count = otherNodes.length;
    otherNodes.forEach((node, index) => {
      const angle = (2 * Math.PI * index) / count;
      node.position = {
        x: centerX + radius * Math.cos(angle) - 40,
        y: centerY + radius * Math.sin(angle) - 40,
      };
    });

    // Assign our custom node type to all nodes
    return updatedNodes.map((node) => ({
      ...node,
      type: "starNode",
    }));
  }, [nodesArray, centerNodeId]);

  // -----------------------------------------------------------------
  // 3. Create edges based on packetFlow data
  // Each edge connects a source IP to its destination IP.
  // -----------------------------------------------------------------
  const edges = useMemo((): Edge[] => {
    return packetFlow?.map((packet: any, index: any) => ({
      id: `e-${packet.source_ip}-${packet.destination_ip}-${index}`, // Fix: Wrap in backticks
      source: packet.source_ip,
      target: packet.destination_ip,
      animated: true,
      type: "smoothstep",
    }));
  }, []);

  // -----------------------------------------------------------------
  // 4. React Flow state management
  // -----------------------------------------------------------------
  const [nodes, setNodes, onNodesChange] = useNodesState(positionedNodes);
  const [edgesState, setEdges, onEdgesChange] = useEdgesState(edges);

  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // -----------------------------------------------------------------
  // 5. Render the React Flow component
  // -----------------------------------------------------------------
  return (
    <div
      style={{ width: "100%", height: "100vh" }}
      className="flex justify-center items-center flex-col"
    >
      <h1 className="text-3xl font-semibold">Ipv4 Connections</h1>
      <ReactFlow
        nodes={nodes}
        edges={edgesState}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background color="#aaa" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
