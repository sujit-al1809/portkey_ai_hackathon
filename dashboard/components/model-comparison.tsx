import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, TrendingDown, TrendingUp } from "lucide-react";

interface ModelComparisonProps {
  models?: Array<{
    name: string;
    avgCost: number;
    avgQuality: number;
    avgLatency: number;
    successRate: number;
    prompts: number;
  }>;
}

export function ModelComparison({ models }: ModelComparisonProps) {
  const modelData = models || [
    {
      name: "GPT-4o-mini",
      avgCost: 0.000152,
      avgQuality: 90,
      avgLatency: 3500,
      successRate: 100,
      prompts: 25,
    },
    {
      name: "GPT-3.5-turbo",
      avgCost: 0.000087,
      avgQuality: 87,
      avgLatency: 1200,
      successRate: 100,
      prompts: 20,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Model Performance Comparison</CardTitle>
        <CardDescription>
          Detailed metrics for each model tested
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Model</TableHead>
              <TableHead className="text-right">Avg Cost</TableHead>
              <TableHead className="text-right">Avg Quality</TableHead>
              <TableHead className="text-right">Avg Latency</TableHead>
              <TableHead className="text-right">Success Rate</TableHead>
              <TableHead className="text-right">Prompts</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {modelData.map((model, index) => (
              <TableRow key={model.name}>
                <TableCell className="font-medium">
                  <div className="flex items-center gap-2">
                    {model.name}
                    {index === 0 && (
                      <Badge variant="secondary" className="text-xs">
                        Current
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-right font-mono">
                  ${model.avgCost.toFixed(6)}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1">
                    {model.avgQuality}%
                    {model.avgQuality >= 90 ? (
                      <TrendingUp className="h-4 w-4 text-green-600" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-orange-600" />
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  {model.avgLatency}ms
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1">
                    {model.successRate}%
                    {model.successRate === 100 && (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  {model.prompts}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
