import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, DollarSign, TrendingUp, Target } from "lucide-react";

interface StatCardsProps {
  data?: {
    totalPrompts: number;
    totalCost: number;
    avgQuality: number;
    costSavings: number;
  };
}

export function StatCards({ data }: StatCardsProps) {
  const stats = data || {
    totalPrompts: 0,
    totalCost: 0,
    avgQuality: 0,
    costSavings: 0,
  };

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Prompts</CardTitle>
          <FileText className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalPrompts}</div>
          <p className="text-xs text-muted-foreground">
            Analyzed across all models
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            ${stats.totalCost.toFixed(4)}
          </div>
          <p className="text-xs text-muted-foreground">All API calls combined</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Quality</CardTitle>
          <Target className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.avgQuality.toFixed(1)}%</div>
          <p className="text-xs text-muted-foreground">Across all responses</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Potential Savings</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {stats.costSavings.toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground">
            By switching models
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
