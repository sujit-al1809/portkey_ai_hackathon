"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface QualityScoresProps {
  data?: {
    accuracy: number;
    helpfulness: number;
    clarity: number;
    completeness: number;
  };
}

export function QualityScores({ data }: QualityScoresProps) {
  const scores = data || {
    accuracy: 92,
    helpfulness: 88,
    clarity: 86,
    completeness: 89,
  };

  const metrics = [
    { name: "Accuracy", value: scores.accuracy, color: "bg-blue-500" },
    { name: "Helpfulness", value: scores.helpfulness, color: "bg-green-500" },
    { name: "Clarity", value: scores.clarity, color: "bg-purple-500" },
    { name: "Completeness", value: scores.completeness, color: "bg-orange-500" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quality Dimensions</CardTitle>
        <CardDescription>
          Average scores across evaluation criteria
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {metrics.map((metric) => (
          <div key={metric.name} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{metric.name}</span>
              <span className="text-sm font-bold">{metric.value}%</span>
            </div>
            <Progress value={metric.value} className="h-3" />
          </div>
        ))}
        
        <div className="mt-6 p-4 bg-muted rounded-lg">
          <p className="text-sm font-medium mb-2">Overall Quality Score</p>
          <p className="text-3xl font-bold text-primary">
            {Object.values(scores).reduce((a, b) => a + b, 0) / 4}%
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Weighted average across all dimensions
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
