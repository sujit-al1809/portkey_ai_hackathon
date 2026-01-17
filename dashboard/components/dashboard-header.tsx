import Link from "next/link";
import { Button } from "@/components/ui/button";
import { RefreshCw, Settings, Download, FlaskConical } from "lucide-react";

export function DashboardHeader() {
  return (
    <header className="border-b bg-card">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              Cost-Quality Optimization Dashboard
            </h1>
            <p className="text-muted-foreground mt-1">
              AI Model Performance & Trade-off Analysis
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/test">
              <Button variant="default" size="sm" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                <FlaskConical className="mr-2 h-4 w-4" />
                Test Prompt
              </Button>
            </Link>
            <Button variant="outline" size="sm">
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
            <Button variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button variant="outline" size="sm">
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
