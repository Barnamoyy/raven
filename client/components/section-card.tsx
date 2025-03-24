import { TrendingUp } from "lucide-react"
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
    status: string; 
    description: string; 
}

const SectionCard:React.FC<SectionCardProps> = ({title,value,status,description}) => {
    return (
        <div className="bg-muted/50 aspect-video rounded-xl">
        <Card className="@container/card">
        <CardHeader className="relative">
          <CardDescription>{title}</CardDescription>
          <CardTitle className="@[250px]/card:text-3xl text-2xl font-semibold tabular-nums">
            {value}
          </CardTitle>
        </CardHeader>
        <CardFooter className="flex-col items-start gap-1 text-sm w-full">
          <div className="line-clamp-1 flex gap-2 font-medium justify-between w-full">
            {status} <TrendingUp className="size-4" />
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