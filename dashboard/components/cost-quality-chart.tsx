"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from "recharts";

interface CostQualityChartProps {
  data?: Array<{
    model: string;
    cost: number;
    quality: number;
    efficiency: number;
  }>;
}

export function CostQualityChart({ data }: CostQualityChartProps) {
  const chartData = data || [
    { model: "GPT-4o-mini", cost: 0.000152, quality: 90, efficiency: 592 },
    { model: "GPT-3.5-turbo", cost: 0.000087, quality: 87, efficiency: 1000 },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cost vs Quality Analysis</CardTitle>
        <CardDescription>
          Compare model performance across cost and quality metrics
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="cost" 
              name="Cost ($)" 
              label={{ value: 'Cost per Request ($)', position: 'bottom' }}
              tickFormatter={(value) => `$${value.toFixed(6)}`}
            />
            <YAxis 
              dataKey="quality" 
              name="Quality" 
              label={{ value: 'Quality Score', angle: -90, position: 'left' }}
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-background border rounded-lg p-3 shadow-lg">
                      <p className="font-medium">{data.model}</p>
                      <p className="text-sm text-muted-foreground">
                        Cost: ${data.cost.toFixed(6)}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Quality: {data.quality}%
                      </p>
                      <p className="text-sm text-primary font-medium">
                        Efficiency: {data.efficiency.toFixed(0)}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Scatter 
              data={chartData} 
              fill="hsl(var(--primary))"
              shape="circle"
              r={8}
            />
          </ScatterChart>
        </ResponsiveContainer>
        <div className="mt-4 text-center">
          <p className="text-sm text-muted-foreground">
            Bubble size represents cost-quality efficiency ratio
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
