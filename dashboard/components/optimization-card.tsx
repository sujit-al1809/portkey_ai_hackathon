import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowRight, TrendingDown, TrendingUp, Lightbulb } from "lucide-react";

interface OptimizationCardProps {
  recommendation: {
    current_model: string;
    recommended_model: string;
    cost_reduction_percent: number;
    quality_impact_percent: number;
    confidence_score: number;
    reasoning: string;
  };
}

export function OptimizationCard({ recommendation }: OptimizationCardProps) {
  const costSavings = recommendation.cost_reduction_percent;
  const qualityImpact = recommendation.quality_impact_percent;
  const confidence = recommendation.confidence_score * 100;

  return (
    <Card className="border-2 border-primary/20">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-primary" />
              Optimization Recommendation
            </CardTitle>
            <CardDescription className="mt-2">
              AI-powered model switching suggestion based on cost-quality analysis
            </CardDescription>
          </div>
          <Badge variant="secondary" className="text-sm">
            {confidence.toFixed(0)}% Confidence
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Model Transition */}
        <div className="flex items-center justify-center gap-4 p-4 bg-muted rounded-lg">
          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-1">Current Model</p>
            <Badge variant="outline" className="text-base px-4 py-2">
              {recommendation.current_model}
            </Badge>
          </div>
          <ArrowRight className="h-6 w-6 text-primary" />
          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-1">Recommended</p>
            <Badge className="text-base px-4 py-2 bg-primary">
              {recommendation.recommended_model}
            </Badge>
          </div>
        </div>

        {/* Impact Metrics */}
        <div className="grid gap-4 md:grid-cols-2">
          <div className="p-4 border rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="h-5 w-5 text-green-600" />
              <span className="text-sm font-medium">Cost Reduction</span>
            </div>
            <p className="text-3xl font-bold text-green-600">
              {costSavings.toFixed(1)}%
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Significant cost savings
            </p>
          </div>

          <div className="p-4 border rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              {qualityImpact < 0 ? (
                <TrendingDown className="h-5 w-5 text-orange-600" />
              ) : (
                <TrendingUp className="h-5 w-5 text-green-600" />
              )}
              <span className="text-sm font-medium">Quality Impact</span>
            </div>
            <p className={`text-3xl font-bold ${qualityImpact < 0 ? 'text-orange-600' : 'text-green-600'}`}>
              {qualityImpact.toFixed(1)}%
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {Math.abs(qualityImpact) < 5 ? "Minimal impact" : "Noticeable change"}
            </p>
          </div>
        </div>

        {/* Reasoning */}
        <div className="p-4 bg-muted rounded-lg">
          <p className="text-sm font-medium mb-2">Analysis</p>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {recommendation.reasoning}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button className="flex-1">Apply Recommendation</Button>
          <Button variant="outline" className="flex-1">
            View Details
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
