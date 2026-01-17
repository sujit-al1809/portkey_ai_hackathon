import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface PromptResultsProps {
  prompts?: Array<{
    id: string;
    content: string;
    bestModel: string;
    quality: number;
    cost: number;
  }>;
}

export function PromptResults({ prompts }: PromptResultsProps) {
  const promptData = prompts || [
    {
      id: "prompt_001",
      content: "Explain quantum computing in simple terms...",
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
    {
      id: "prompt_003",
      content: "Write a Python function to sort a list...",
      bestModel: "GPT-3.5-turbo",
      quality: 95,
      cost: 0.000121,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prompt Analysis Results</CardTitle>
        <CardDescription>
          Recent prompts tested across models
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px]">
          <div className="space-y-4">
            {promptData.map((prompt) => (
              <div
                key={prompt.id}
                className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <p className="text-sm font-medium line-clamp-1">
                    {prompt.content}
                  </p>
                  <Badge variant="outline" className="shrink-0 text-xs">
                    {prompt.id}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Best: </span>
                    <span className="font-medium">{prompt.bestModel}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Quality: </span>
                    <span className="font-medium text-green-600">
                      {prompt.quality}%
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Cost: </span>
                    <span className="font-mono text-xs">
                      ${prompt.cost.toFixed(6)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
