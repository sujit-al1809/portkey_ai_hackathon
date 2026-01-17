"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

export function TestHeader() {
  return (
    <header className="border-b bg-card sticky top-0 z-50 backdrop-blur-sm bg-white/80 dark:bg-slate-950/80">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Dashboard
              </Button>
            </Link>
            <div className="h-6 w-px bg-slate-200 dark:bg-slate-700" />
            <div>
              <h1 className="text-2xl font-bold tracking-tight">
                Prompt Optimizer
              </h1>
              <p className="text-muted-foreground text-sm mt-0.5">
                Test any prompt and get intelligent model recommendations
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
