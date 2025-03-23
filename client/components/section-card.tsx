import {TimerResetIcon, TrendingUpDown } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

import React from 'react';

interface SectionCardProps {
    title: string; 
    value: string; 
    percentage: string; 
    status: string; 
    description: string; 
}

const SectionCard:React.FC<SectionCardProps> = ({title,value,percentage,status,description}) => {
    return (
        <div className="bg-muted/50 aspect-video rounded-xl">
        <Card className="@container/card">
        <CardHeader className="relative">
          <CardDescription>{title}</CardDescription>
          <CardTitle className="@[250px]/card:text-3xl text-2xl font-semibold tabular-nums">
            {value}
          </CardTitle>
          <div className="absolute right-4 top-4">
            <Badge variant="outline" className="flex gap-1 rounded-lg text-xs">
              <TrendingUpDown className="size-3" />
              {percentage}
            </Badge>
          </div>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1 text-sm">
          <div className="line-clamp-1 flex gap-2 font-medium">
            {status} <TimerResetIcon className="size-4" />
          </div>
          <div className="text-muted-foreground">
            {description}
          </div>
        </CardFooter>
      </Card>
        </div>
    );
}

export default SectionCard;