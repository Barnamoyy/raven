"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import type { Packet } from "@/components/data/packets"
import { DataTableColumnHeader } from "./data-table-column-header"

export const packetColumns: ColumnDef<Packet>[] = [
  {
    accessorKey: "packetNumber",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Packet Number" />,
    cell: ({ row }) => <div className="font-medium">{row.getValue("packetNumber")}</div>,
    enableSorting: true,
    enableHiding: true,
  },
  {
    accessorKey: "sourceIp",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Source IP" />,
    cell: ({ row }) => <div>{row.getValue("sourceIp")}</div>,
    enableSorting: true,
    enableHiding: true,
  },
  {
    accessorKey: "destinationIp",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Destination IP" />,
    cell: ({ row }) => <div>{row.getValue("destinationIp")}</div>,
    enableSorting: true,
    enableHiding: true,
  },
  {
    accessorKey: "port",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Port" />,
    cell: ({ row }) => <div>{row.getValue("port")}</div>,
    enableSorting: true,
    enableHiding: true,
  },
  {
    accessorKey: "packetSize",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Packet Size" />,
    cell: ({ row }) => <div>{row.getValue("packetSize")} bytes</div>,
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
    accessorKey: "delay",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Delay" />,
    cell: ({ row }) => row.getValue("delay") as string,
    enableSorting: true,
    enableHiding: true,
  },
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

