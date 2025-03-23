"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import type { Packet } from "@/components/data/packets"
import { DataTableColumnHeader } from "./data-table-column-header"

export const packetColumns: ColumnDef<Packet>[] = [
  {
    accessorKey: "packet_id",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Packet Number" />,
    cell: ({ row }) => <div className="font-medium">{row.getValue("packet_id")}</div>,
    enableSorting: true,
    enableHiding: true,
  },
  {
    accessorKey: "src_ip",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Source IP" />,
    cell: ({ row }) => <div>{row.getValue("src_ip")}</div>,
    enableSorting: true,
    enableHiding: true,
  },
  {
    accessorKey: "dst_ip",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Destination IP" />,
    cell: ({ row }) => <div>{row.getValue("dst_ip")}</div>,
    enableSorting: true,
    enableHiding: true,
  },
  {
    accessorKey: "dst_port",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Port" />,
    cell: ({ row }) => <div>{row.getValue("dst_port")}</div>,
    enableSorting: true,
    enableHiding: true,
  },
  {
    accessorKey: "size",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Packet Size" />,
    cell: ({ row }) => <div>{row.getValue("size")} bytes</div>,
    enableSorting: true,
    enableHiding: true,
  },
  {
    accessorKey: "protocol",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Protocol" />,
    cell: ({ row }) => {
      const protocol = row.getValue("protocol") as string
      return protocol
    },
    enableSorting: true,
    enableHiding: true,
    filterFn: (row, id, value) => {
      return value.includes(row.getValue(id))
    },
  },
  {
    accessorKey: "packet_type",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Delay" />,
    cell: ({ row }) => {
      const packetType = row.getValue("packet_type") as Record<string, boolean>;
  
      if (!packetType) return <div>No Data</div>; // Handle missing data
  
      // Filter out the true values and join them into a string
      const activeDelays = Object.keys(packetType)
        .filter((key) => packetType[key])
        .join(", ");
  
      return <div>{activeDelays || "No Delays"}</div>;
    },
    enableSorting: true,
    enableHiding: true,
  }
  
]

function getProtocolVariant(protocol: string): "default" | "secondary" | "destructive" | "outline" {
  switch (protocol.toLowerCase()) {
    case "tcp":
      return "default"
    case "udp":
      return "secondary"
    case "icmp":
      return "destructive"
    default:
      return "outline"
  }
}


