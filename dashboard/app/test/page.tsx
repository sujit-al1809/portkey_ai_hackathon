"use client"

export const dynamic = "force-dynamic";

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { TestHeader } from "@/components/test-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Send, AlertCircle, CheckCircle2, TrendingDown, TrendingUp, Zap, DollarSign, Target, LogOut, History } from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// Knowledge cutoff dates for models
const MODEL_CUTOFFS: Record<string, string> = {
  "gpt-4o": "April 2024",
  "gpt-4-turbo": "April 2024",
  "gpt-3.5-turbo": "April 2023",
  "claude-3-5-sonnet": "June 2024",
  "claude-3-opus": "February 2024",
  "llama-2-70b": "July 2023",
  "mistral-7b": "December 2023",
  "command-r": "March 2024",
  "palm-2": "December 2023",
}

// Component to display knowledge cutoff info
function KnowledgeCutoffBadge({ modelName }: { modelName: string }) {
  const normalizedName = modelName.toLowerCase()
  const cutoff = MODEL_CUTOFFS[normalizedName] || "Unknown"
  
  return (
    <span className="inline-block bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-xs">
      📅 Knowledge cutoff: <strong>{cutoff}</strong>
    </span>
  )
}

interface ModelResult {
  model_name: string
  quality_score: number
  cost: number
  latency_ms: number
  response: string
  success: boolean
  is_cached?: boolean
}

interface AnalysisResult {
  use_case: string
  recommended_model: string
  reasoning: string
  cost_savings_percent: number
  quality_impact_percent: number
  models: ModelResult[]
  timestamp: string
  status?: string
  message?: string
  cached_from?: string
  is_cached?: boolean
  original_question?: string
  quality_score?: number
  fallback_note?: string
}

interface HistoryChat {
  question: string
  model: string
  quality: number
  cost: number
  date: string
}

interface OptimizationResult {
  status: string
  summary: string
  recommendation: {
    current_model: string
    recommended_model: string
    recommended_model_display: string
    projected_cost_saving_percent: number
    projected_quality_impact_percent: number
    confidence: number
    business_impact: {
      monthly_request_volume: number
      current_monthly_cost_usd: number
      projected_monthly_cost_usd: number
      projected_monthly_savings_usd: number
      annual_savings_usd: number
    }
    reasons: string[]
    fallback_option?: {
      model: string
      cost_saving_percent: number
      quality_impact_percent: number
    }
  }
  processing_time_seconds: number
  verification_cost_usd: number
}

export default function TestPage() {
  const router = useRouter()
  const [username, setUsername] = useState<string>("")
  const [userId, setUserId] = useState<string>("")
  const [sessionId, setSessionId] = useState<string>("")
  const [checkingAuth, setCheckingAuth] = useState(true)
  
  const [prompt, setPrompt] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<string>("")
  const [autoMode, setAutoMode] = useState(true)  // Auto mode toggle
  
  // History state
  const [showHistory, setShowHistory] = useState(false)
  const [history, setHistory] = useState<HistoryChat[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  
  // Optimization state
  const [optimizing, setOptimizing] = useState(false)
  const [optimizationResult, setOptimizationResult] = useState<any>(null)
  const [optimizationError, setOptimizationError] = useState<string | null>(null)

  // Check authentication on mount
  useEffect(() => {
    const storedSessionId = localStorage.getItem('session_id')
    const storedUsername = localStorage.getItem('username')
    const storedUserId = localStorage.getItem('user_id')
    
    if (!storedSessionId || !storedUsername || !storedUserId) {
      router.push('/login')
    } else {
      setSessionId(storedSessionId)
      setUsername(storedUsername)
      setUserId(storedUserId)
      setCheckingAuth(false)
    }
  }, [router])

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      })
    } catch (err) {
      console.error('Logout error:', err)
    }
    
    localStorage.removeItem('session_id')
    localStorage.removeItem('username')
    localStorage.removeItem('user_id')
    router.push('/login')
  }

  const loadHistory = async () => {
    if (history.length > 0) {
      setShowHistory(!showHistory)
      return
    }
    
    setHistoryLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/history/${userId}`, {
        headers: { 'Authorization': `Bearer ${sessionId}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setHistory(data.chats || [])
        setShowHistory(true)
      }
    } catch (err) {
      console.error('Failed to load history:', err)
    } finally {
      setHistoryLoading(false)
    }
  }

  const handleOptimize = async () => {
    setOptimizing(true)
    setOptimizationError(null)
    setOptimizationResult(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/optimize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_id: userId }),
      })

      if (!response.ok) {
        throw new Error("Optimization failed")
      }

      const data = await response.json()
      setOptimizationResult(data)
    } catch (err) {
      setOptimizationError("Failed to run optimization. Make sure the backend is running on port 5000.")
      console.error(err)
    } finally {
      setOptimizing(false)
    }
  }

  const handleAnalyze = async () => {
    if (!prompt.trim()) {
      setError("Please enter a prompt")
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    
    const endpoint = autoMode ? '/auto' : '/analyze'
    const progressMessages = autoMode 
      ? ["🚀 Auto Mode - Finding best model...", "⚡ Selecting optimal response..."]
      : ["🔍 Detecting use case...", "🔄 Testing across models...", "📊 Running quality evaluation...", "💰 Calculating cost-quality trade-offs..."]
    
    setProgress(progressMessages[0])

    try {
      progressMessages.forEach((msg, idx) => {
        setTimeout(() => setProgress(msg), idx * 2000)
      })
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: prompt.trim(), user_id: userId }),
      })

      if (!response.ok) {
        throw new Error("Analysis failed")
      }

      const data = await response.json()
      setProgress(data.status === 'cached' ? "⚡ Cached response retrieved!" : "✅ Complete!")
      setTimeout(() => setProgress(""), 1000)
      setResult(data)
      
      // Refresh history if new chat was saved
      if (data.status !== 'cached') {
        setHistory([])
      }
    } catch (err) {
      setError("Failed to analyze prompt. Make sure the backend is running.")
      console.error(err)
      setProgress("")
    } finally {
      setLoading(false)
    }
  }

  if (checkingAuth) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <Loader2 className="animate-spin" size={40} />
      </div>
    )
  }

  const getUseCaseBadgeColor = (useCase: string) => {
    if (!useCase) return "bg-gray-500"
    const lowerCase = useCase.toLowerCase()
    if (lowerCase.includes("code")) return "bg-blue-500"
    if (lowerCase.includes("security")) return "bg-red-500"
    if (lowerCase.includes("creative")) return "bg-purple-500"
    return "bg-green-500"
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <TestHeader />
      
      {/* User Info & Logout */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '16px',
        marginBottom: '20px'
      }}>
        <div className="container mx-auto px-4 max-w-7xl">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <p style={{ margin: '0', fontSize: '14px', opacity: 0.9 }}>Logged in as</p>
              <p style={{ margin: '0', fontSize: '18px', fontWeight: '600' }}>{username}</p>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <Button
                onClick={loadHistory}
                disabled={historyLoading}
                variant="outline"
                size="sm"
                style={{
                  background: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  borderColor: 'white'
                }}
              >
                <History size={16} style={{ marginRight: '6px' }} />
                {history.length > 0 ? `History (${history.length})` : 'View History'}
              </Button>
              <Button
                onClick={handleLogout}
                variant="outline"
                size="sm"
                style={{
                  background: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  borderColor: 'white'
                }}
              >
                <LogOut size={16} style={{ marginRight: '6px' }} />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-7xl">

        {/* History Section */}
        {showHistory && (
          <Card className="mb-6 shadow-lg border-amber-200 dark:border-amber-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <History size={20} />
                  Conversation History
                </CardTitle>
                <Button
                  variant="ghost"
                  onClick={() => setShowHistory(false)}
                  size="sm"
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {history.length === 0 ? (
                <p className="text-gray-500">No previous conversations yet. Ask your first question!</p>
              ) : (
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  {history.map((chat, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '12px',
                        marginBottom: '12px',
                        background: '#f9f9f9',
                        borderRadius: '6px',
                        borderLeft: '3px solid #667eea'
                      }}
                    >
                      <p style={{ margin: '0 0 6px 0', fontSize: '14px', fontWeight: '500' }}>
                        Q: {chat.question.substring(0, 100)}{chat.question.length > 100 ? '...' : ''}
                      </p>
                      <div style={{ display: 'flex', gap: '12px', fontSize: '13px', color: '#666' }}>
                        <span>Model: {chat.model}</span>
                        <span>Quality: {(chat.quality * 100).toFixed(0)}%</span>
                        <span>Cost: ${chat.cost.toFixed(4)}</span>
                        <span>{new Date(chat.date).toLocaleDateString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Result or Cached Response Notification */}
        {result && result.status === 'cached' && (
          <Card className="mb-6 shadow-lg border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-700 dark:text-green-300">
                <CheckCircle2 size={20} />
                Cached Response Found!
              </CardTitle>
              <CardDescription className="text-green-600 dark:text-green-400">
                {result.message}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                {result.original_question && (
                  <p><strong>Original Question:</strong> {result.original_question}</p>
                )}
                <p><strong>Model Used:</strong> {result.recommended_model}</p>
                {result.quality_score && (
                  <p><strong>Quality Score:</strong> {(result.quality_score * 100).toFixed(0)}%</p>
                )}
                <p><strong>Cost Saved:</strong> $0.00 (cached)</p>
                {result.cached_from && (
                  <p><strong>Retrieved From:</strong> {result.cached_from}</p>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Optimization Section - Track 4 Feature */}
        <Card className="mb-6 shadow-lg border-2 border-purple-200 dark:border-purple-800 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/30 dark:to-blue-950/30">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-2xl">
                  <Zap className="h-6 w-6 text-purple-600" />
                  Cost-Quality Optimization
                </CardTitle>
                <CardDescription className="text-base mt-1">
                  Multi-agent system analyzes your usage and recommends cost-saving model switches
                </CardDescription>
              </div>
              <Button
                onClick={handleOptimize}
                disabled={optimizing}
                size="lg"
                className="bg-purple-600 hover:bg-purple-700"
              >
                {optimizing ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Optimizing...
                  </>
                ) : (
                  <>
                    <Target className="mr-2 h-5 w-5" />
                    Run Optimization
                  </>
                )}
              </Button>
            </div>
          </CardHeader>
          
          {optimizationError && (
            <CardContent>
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                <p className="text-red-800 dark:text-red-200">{optimizationError}</p>
              </div>
            </CardContent>
          )}
          
          {optimizationResult && optimizationResult.status === "success" && (
            <CardContent className="space-y-4">
              {/* Recommendation Banner */}
              <div className="p-4 bg-gradient-to-r from-green-100 to-emerald-100 dark:from-green-900/40 dark:to-emerald-900/40 rounded-lg border-2 border-green-300 dark:border-green-700">
                <p className="text-lg font-bold text-green-800 dark:text-green-200">
                  💡 Switching from {optimizationResult.recommendation.current_model} to {optimizationResult.recommendation.recommended_model} reduces cost by {optimizationResult.recommendation.projected_cost_saving_percent.toFixed(1)}% with a {Math.abs(optimizationResult.recommendation.projected_quality_impact_percent).toFixed(1)}% quality impact.
                </p>
              </div>
              
              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="p-3 bg-white dark:bg-slate-800 rounded-lg border shadow-sm">
                  <div className="flex items-center gap-1 mb-2">
                    <TrendingDown className="h-4 w-4 text-green-600" />
                    <span className="text-xs text-slate-600 dark:text-slate-400">Cost Savings</span>
                  </div>
                  <p className="text-2xl font-bold text-green-600">
                    {optimizationResult.recommendation.projected_cost_saving_percent.toFixed(1)}%
                  </p>
                </div>
                
                <div className="p-3 bg-white dark:bg-slate-800 rounded-lg border shadow-sm">
                  <div className="flex items-center gap-1 mb-2">
                    <TrendingUp className="h-4 w-4 text-orange-600" />
                    <span className="text-xs text-slate-600 dark:text-slate-400">Quality Impact</span>
                  </div>
                  <p className="text-2xl font-bold text-orange-600">
                    {Math.abs(optimizationResult.recommendation.projected_quality_impact_percent).toFixed(1)}%
                  </p>
                </div>
                
                <div className="p-3 bg-white dark:bg-slate-800 rounded-lg border shadow-sm">
                  <div className="flex items-center gap-1 mb-2">
                    <DollarSign className="h-4 w-4 text-blue-600" />
                    <span className="text-xs text-slate-600 dark:text-slate-400">Monthly Savings</span>
                  </div>
                  <p className="text-2xl font-bold text-blue-600">
                    ${optimizationResult.monthly_savings_estimate?.toFixed(2) || "0.00"}
                  </p>
                </div>
                
                <div className="p-3 bg-white dark:bg-slate-800 rounded-lg border shadow-sm">
                  <div className="flex items-center gap-1 mb-2">
                    <CheckCircle2 className="h-4 w-4 text-purple-600" />
                    <span className="text-xs text-slate-600 dark:text-slate-400">Confidence</span>
                  </div>
                  <p className="text-2xl font-bold text-purple-600">
                    {optimizationResult.recommendation.confidence}%
                  </p>
                </div>
              </div>
              
              {/* All Models Comparison */}
              <div>
                <h4 className="font-semibold mb-3 text-lg">All Models Comparison</h4>
                <div className="grid grid-cols-1 gap-3">
                  {optimizationResult.models && optimizationResult.models.length > 0 ? (
                    optimizationResult.models.map((model: any, idx: number) => (
                      <div
                        key={idx}
                        className={`p-4 rounded-lg border-2 transition ${
                          model.model_name === optimizationResult.recommendation.recommended_model
                            ? 'border-green-400 bg-green-50 dark:border-green-600 dark:bg-green-900/20'
                            : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <h5 className="font-semibold text-lg">{model.model_name}</h5>
                            {model.model_name === optimizationResult.recommendation.recommended_model && (
                              <Badge className="bg-green-500 text-white">Recommended</Badge>
                            )}
                          </div>
                          <Badge variant={model.success ? "default" : "destructive"}>
                            {model.success ? "✓ Success" : "✗ Failed"}
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-3 mb-2">
                          <div>
                            <p className="text-xs text-slate-500 dark:text-slate-400">Quality</p>
                            <p className="text-xl font-bold text-slate-800 dark:text-slate-200">{model.quality_score.toFixed(0)}</p>
                            <p className="text-xs text-slate-500">/ 100</p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500 dark:text-slate-400">Cost</p>
                            <p className="text-xl font-bold text-slate-800 dark:text-slate-200">${model.cost.toFixed(6)}</p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500 dark:text-slate-400">Speed</p>
                            <p className="text-xl font-bold text-slate-800 dark:text-slate-200">{model.latency_ms.toFixed(0)}</p>
                            <p className="text-xs text-slate-500">ms</p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center p-4 text-slate-500">No models to display</div>
                  )}
                </div>
              </div>
              
              {/* Processing Info */}
              <div className="text-xs text-slate-500 text-right">
                Processed in {optimizationResult.processing_time_seconds?.toFixed(2) || "0.1"}s | 
                Verification cost: ${optimizationResult.verification_cost_usd?.toFixed(6) || "0.000000"}
              </div>
            </CardContent>
          )}
          
          {optimizationResult && optimizationResult.status === "no_recommendation" && (
            <CardContent>
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200">
                <p className="text-blue-800 dark:text-blue-200">
                  ✓ Your current model appears to be optimal for your use case and constraints.
                </p>
              </div>
            </CardContent>
          )}
        </Card>

        <hr className="my-8 border-slate-300 dark:border-slate-700" />

        {/* Input Section */}
        <Card className="mb-6 shadow-lg">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Test Your Prompt</CardTitle>
                <CardDescription>
                  System will analyze and recommend the best model for your use case
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  {autoMode ? "🚀 Auto Mode" : "📊 Full Analysis"}
                </span>
                <button
                  onClick={() => setAutoMode(!autoMode)}
                  className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                    autoMode ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                      autoMode ? 'translate-x-7' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
                <p className="text-sm text-slate-700 dark:text-slate-300">
                  {autoMode ? (
                    <>
                      <strong>Auto Mode:</strong> Automatically selects the best model based on cost, quality, and knowledge cutoff. Just get the answer!
                    </>
                  ) : (
                    <>
                      <strong>Full Analysis:</strong> See detailed breakdown of all models tested, quality scores, costs, and trade-off analysis.
                    </>
                  )}
                </p>
              </div>
              
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
                    {autoMode ? "Finding best model..." : "Analyzing..."}
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-5 w-5" />
                    {autoMode ? "Get Answer" : "Full Analysis"}
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
                    {autoMode ? "Finding the best model..." : "Testing multiple models + quality evaluation..."}
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

        {/* Auto Mode Result */}
        {result && autoMode && (result as any).mode === 'auto' && (
          <Card className="mb-6 shadow-lg border-2 border-green-400 dark:border-green-600 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-2xl text-green-800 dark:text-green-200">
                <Zap className="h-6 w-6" />
                Auto Mode Result
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Answer */}
                <div className="p-4 bg-white dark:bg-slate-900 rounded-lg border-2 border-green-200 dark:border-green-800">
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">Answer from {(result as any).model_used}:</p>
                  <p className="text-lg text-slate-800 dark:text-slate-200 leading-relaxed">
                    {(result as any).answer}
                  </p>
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
                    <p className="text-xs text-slate-600 dark:text-slate-400">Quality</p>
                    <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                      {((result as any).summary?.quality?.score || 0).toFixed(0)}%
                    </p>
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                      {(result as any).summary?.quality?.level}
                    </p>
                  </div>

                  <div className="p-3 bg-green-100 dark:bg-green-900/50 rounded-lg">
                    <p className="text-xs text-slate-600 dark:text-slate-400">Cost</p>
                    <p className="text-2xl font-bold text-green-700 dark:text-green-300">
                      ${((result as any).summary?.cost?.amount || 0).toFixed(6)}
                    </p>
                    <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                      {(result as any).summary?.cost?.level}
                    </p>
                  </div>

                  <div className="p-3 bg-purple-100 dark:bg-purple-900/50 rounded-lg">
                    <p className="text-xs text-slate-600 dark:text-slate-400">Speed</p>
                    <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                      {((result as any).summary?.latency_ms || 0).toFixed(0)}ms
                    </p>
                    <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">Latency</p>
                  </div>

                  <div className="p-3 bg-amber-100 dark:bg-amber-900/50 rounded-lg">
                    <p className="text-xs text-slate-600 dark:text-slate-400">Score</p>
                    <p className="text-2xl font-bold text-amber-700 dark:text-amber-300">
                      {(((result as any).summary?.overall_score || 0) * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">Overall</p>
                  </div>
                </div>

                {/* Selection Reason */}
                <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg border-l-4 border-green-500">
                  <p className="text-sm text-slate-700 dark:text-slate-300">
                    <strong>Why {(result as any).model_used}?</strong> {(result as any).model_selection_reason}
                  </p>
                </div>

                {/* Alternatives */}
                {(result as any).alternatives && (result as any).alternatives.length > 0 && (
                  <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Other options:</p>
                    <div className="flex gap-2 flex-wrap">
                      {(result as any).alternatives.map((alt: any, idx: number) => (
                        <span key={idx} className="text-xs bg-white dark:bg-slate-800 px-2 py-1 rounded border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400">
                          {alt.model}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

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
                    
                    {(result as any).fallback_note && (
                      <div className="mt-3 p-3 bg-amber-50 dark:bg-amber-900/30 border-l-4 border-amber-500 rounded">
                        <p className="text-sm text-amber-800 dark:text-amber-200 flex items-start gap-2">
                          <span className="text-lg">⚠️</span>
                          <span><strong>Knowledge Cutoff:</strong> {(result as any).fallback_note}</span>
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
                      <div className="flex items-center gap-2 mb-2">
                        <TrendingDown className="h-5 w-5 text-green-600 dark:text-green-400" />
                        <h4 className="font-semibold text-green-800 dark:text-green-200">Cost Savings</h4>
                      </div>
                      <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                        {(result.cost_savings_percent ?? result.cost_savings_percent !== undefined ? result.cost_savings_percent : 0).toFixed(1)}%
                      </p>
                      <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                        {result.status === 'cached' ? 'Cached response (100% saved!)' : 'Potential reduction'}
                      </p>
                    </div>

                    <div className="p-4 bg-orange-50 dark:bg-orange-950/30 rounded-lg border border-orange-200 dark:border-orange-800">
                      <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                        <h4 className="font-semibold text-orange-800 dark:text-orange-200">Quality Impact</h4>
                      </div>
                      <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                        {(result.quality_impact_percent ?? 0).toFixed(1)}%
                      </p>
                      <p className="text-sm text-orange-700 dark:text-orange-300 mt-1">
                        {result.status === 'cached' ? 'No new analysis needed' : (result.quality_impact_percent > 0 ? "Improvement" : "Trade-off")}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Cached Response Notification */}
            {result.status === 'cached' && (
              <Card className="shadow-lg border-2 border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-amber-900 dark:text-amber-100">
                    <Zap className="h-5 w-5 text-amber-600" />
                    Cached Response
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-amber-900 dark:text-amber-100 mb-2">
                    <strong>Similar question found in your history!</strong>
                  </p>
                  <p className="text-sm text-amber-800 dark:text-amber-200 mb-3">
                    Original question: <em>"{result.original_question}"</em>
                  </p>
                  <p className="text-sm text-amber-800 dark:text-amber-200">
                    Model used: <strong>{result.recommended_model}</strong> | Quality: <strong>{((result.quality_score ?? 0) * 100).toFixed(0)}/100</strong>
                  </p>
                </CardContent>
              </Card>
            )}
            {result.models && (
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
                          
                          {/* Knowledge Cutoff Info */}
                          <div className="mt-3 text-xs text-slate-500 dark:text-slate-400">
                            <KnowledgeCutoffBadge modelName={model.model_name} />
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
