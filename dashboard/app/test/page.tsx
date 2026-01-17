"use client"

import { useState } from "react"
import { TestHeader } from "@/components/test-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Send, AlertCircle, CheckCircle2, TrendingDown, TrendingUp } from "lucide-react"

interface ModelResult {
  model_name: string
  quality_score: number
  cost: number
  latency_ms: number
  response: string
  success: boolean
}

interface AnalysisResult {
  use_case: string
  recommended_model: string
  reasoning: string
  cost_savings_percent: number
  quality_impact_percent: number
  models: ModelResult[]
  timestamp: string
}

export default function TestPage() {
  const [prompt, setPrompt] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<string>("")

  const handleAnalyze = async () => {
    if (!prompt.trim()) {
      setError("Please enter a prompt")
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    setProgress("🔍 Detecting use case...")

    try {
      setTimeout(() => setProgress("🔄 Testing across models (GPT-4o-mini, GPT-3.5-turbo)..."), 500)
      setTimeout(() => setProgress("📊 Running quality evaluation (LLM-as-judge)..."), 3000)
      setTimeout(() => setProgress("💰 Calculating cost-quality trade-offs..."), 6000)
      
      const response = await fetch("http://localhost:5000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: prompt.trim() }),
      })

      if (!response.ok) {
        throw new Error("Analysis failed")
      }

      const data = await response.json()
      setProgress("✅ Analysis complete!")
      setTimeout(() => setProgress(""), 1000)
      setResult(data)
    } catch (err) {
      setError("Failed to analyze prompt. Make sure the backend is running.")
      console.error(err)
      setProgress("")
    } finally {
      setLoading(false)
    }
  }

  const getUseCaseBadgeColor = (useCase: string) => {
    const lowerCase = useCase.toLowerCase()
    if (lowerCase.includes("code")) return "bg-blue-500"
    if (lowerCase.includes("security")) return "bg-red-500"
    if (lowerCase.includes("creative")) return "bg-purple-500"
    return "bg-green-500"
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <TestHeader />
      <div className="container mx-auto px-4 py-8 max-w-7xl">

        {/* Input Section */}
        <Card className="mb-6 shadow-lg">
          <CardHeader>
            <CardTitle>Test Your Prompt</CardTitle>
            <CardDescription>
              System will analyze and recommend the best model for your use case
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter your prompt here... (e.g., 'Write a Python function for binary search' or 'Analyze this code for security issues')"
                className="w-full min-h-[120px] p-4 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                disabled={loading}
              />
              <Button
                onClick={handleAnalyze}
                disabled={loading || !prompt.trim()}
                className="w-full sm:w-auto"
                size="lg"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-5 w-5" />
                    Analyze Prompt
                  </>
                )}
              </Button>
            </div>

            {loading && progress && (
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg flex items-start gap-3">
                <Loader2 className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 animate-spin" />
                <div>
                  <p className="text-blue-800 dark:text-blue-200 font-medium">{progress}</p>
                  <p className="text-blue-600 dark:text-blue-400 text-sm mt-1">
                    This takes 10-15 seconds (testing multiple models + quality evaluation)
                  </p>
                </div>
              </div>
            )}

            {error && (
              <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                <p className="text-red-800 dark:text-red-200">{error}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Section */}
        {result && (
          <div className="space-y-6">
            {/* Use Case & Recommendation */}
            <Card className="shadow-lg border-2 border-blue-200 dark:border-blue-800">
              <CardHeader>
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div>
                    <CardTitle className="text-2xl mb-2">Recommendation</CardTitle>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-slate-600 dark:text-slate-400">Detected Use Case:</span>
                      <Badge className={getUseCaseBadgeColor(result.use_case)}>
                        {result.use_case}
                      </Badge>
                    </div>
                  </div>
                  <CheckCircle2 className="h-12 w-12 text-green-500" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 rounded-lg border border-blue-200 dark:border-blue-800">
                    <h3 className="font-semibold text-lg mb-2">🎯 Best Model: {result.recommended_model}</h3>
                    <p className="text-slate-700 dark:text-slate-300">{result.reasoning}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
                      <div className="flex items-center gap-2 mb-2">
                        <TrendingDown className="h-5 w-5 text-green-600 dark:text-green-400" />
                        <h4 className="font-semibold text-green-800 dark:text-green-200">Cost Savings</h4>
                      </div>
                      <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                        {result.cost_savings_percent.toFixed(1)}%
                      </p>
                      <p className="text-sm text-green-700 dark:text-green-300 mt-1">Potential reduction</p>
                    </div>

                    <div className="p-4 bg-orange-50 dark:bg-orange-950/30 rounded-lg border border-orange-200 dark:border-orange-800">
                      <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                        <h4 className="font-semibold text-orange-800 dark:text-orange-200">Quality Impact</h4>
                      </div>
                      <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                        {Math.abs(result.quality_impact_percent).toFixed(1)}%
                      </p>
                      <p className="text-sm text-orange-700 dark:text-orange-300 mt-1">
                        {result.quality_impact_percent > 0 ? "Improvement" : "Trade-off"}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Model Comparison */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Model Comparison</CardTitle>
                <CardDescription>Detailed results from all tested models</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {result.models.map((model, idx) => (
                    <div
                      key={idx}
                      className={`p-4 rounded-lg border-2 ${
                        model.model_name === result.recommended_model
                          ? "border-blue-500 bg-blue-50 dark:bg-blue-950/30"
                          : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900"
                      }`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-lg flex items-center gap-2">
                            {model.model_name}
                            {model.model_name === result.recommended_model && (
                              <Badge className="bg-blue-500">Recommended</Badge>
                            )}
                          </h4>
                        </div>
                        <Badge variant={model.success ? "default" : "destructive"}>
                          {model.success ? "Success" : "Failed"}
                        </Badge>
                      </div>

                      {model.success && (
                        <>
                          <div className="grid grid-cols-3 gap-4 mb-3">
                            <div>
                              <p className="text-sm text-slate-600 dark:text-slate-400">Quality</p>
                              <p className="text-xl font-bold">{model.quality_score}/100</p>
                            </div>
                            <div>
                              <p className="text-sm text-slate-600 dark:text-slate-400">Cost</p>
                              <p className="text-xl font-bold">${model.cost.toFixed(6)}</p>
                            </div>
                            <div>
                              <p className="text-sm text-slate-600 dark:text-slate-400">Latency</p>
                              <p className="text-xl font-bold">{model.latency_ms.toFixed(0)}ms</p>
                            </div>
                          </div>

                          <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700">
                            <p className="text-sm font-medium mb-1">Response Preview:</p>
                            <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-3">
                              {model.response}
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
