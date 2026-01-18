"use client";

export const dynamic = "force-dynamic";

import { useState, useEffect } from "react";
import { DashboardHeader } from "@/components/dashboard-header";
import { OptimizationCard } from "@/components/optimization-card";
import { ModelComparison } from "@/components/model-comparison";
import { CostQualityChart } from "@/components/cost-quality-chart";
import { QualityScores } from "@/components/quality-scores";
import { PromptResults } from "@/components/prompt-results";
import { StatCards } from "@/components/stat-cards";
import { RecentActivity } from "@/components/recent-activity";

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load data from Python backend JSON files
    const loadData = async () => {
      try {
        const response = await fetch("/api/dashboard-data");
        const jsonData = await response.json();
        setData(jsonData);
      } catch (error) {
        console.error("Error loading data:", error);
        // Load mock data for demo
        setData(getMockData());
      } finally {
        setLoading(false);
      }
    };

    loadData();
    // Refresh every 10 seconds
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />
      
      <main className="container mx-auto p-6 space-y-6">
        {/* Stats Overview */}
        <StatCards data={data?.stats} />

        {/* Optimization Recommendation */}
        {data?.recommendation && (
          <OptimizationCard recommendation={data.recommendation} />
        )}

        {/* Charts Row */}
        <div className="grid gap-6 md:grid-cols-2">
          <CostQualityChart data={data?.chartData} />
          <QualityScores data={data?.qualityScores} />
        </div>

        {/* Model Comparison */}
        <ModelComparison models={data?.models} />

        {/* Bottom Row */}
        <div className="grid gap-6 md:grid-cols-2">
          <PromptResults prompts={data?.prompts} />
          <RecentActivity activities={data?.activities} />
        </div>
      </main>
    </div>
  );
}

// Mock data for demo
function getMockData() {
  return {
    stats: {
      totalPrompts: 45,
      totalCost: 0.0234,
      avgQuality: 88.5,
      costSavings: 42.3,
    },
    recommendation: {
      current_model: "GPT-4o-mini",
      recommended_model: "GPT-3.5-turbo",
      cost_reduction_percent: 42.3,
      quality_impact_percent: -3.2,
      confidence_score: 0.87,
      reasoning: "Based on 45 prompts analyzed, switching to GPT-3.5-turbo reduces costs by 42.3% with only a 3.2% quality decrease.",
    },
    chartData: [
      { model: "GPT-4o-mini", cost: 0.000152, quality: 90, efficiency: 592 },
      { model: "GPT-3.5-turbo", cost: 0.000087, quality: 87, efficiency: 1000 },
    ],
    qualityScores: {
      accuracy: 92,
      helpfulness: 88,
      clarity: 86,
      completeness: 89,
    },
    models: [
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
    ],
    prompts: [
      {
        id: "prompt_001",
        content: "Explain quantum computing...",
        bestModel: "GPT-4o-mini",
        quality: 92,
        cost: 0.000152,
      },
      {
        id: "prompt_002",
        content: "What is 2+2?",
        bestModel: "GPT-3.5-turbo",
        quality: 100,
        cost: 0.000037,
      },
    ],
    activities: [
      {
        type: "analysis",
        message: "Analyzed 5 new prompts",
        time: "2 minutes ago",
      },
      {
        type: "recommendation",
        message: "New optimization recommendation available",
        time: "15 minutes ago",
      },
    ],
  };
}
