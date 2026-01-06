import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Send, History, Zap, Brain } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
}

export default function Copilot() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: "1",
            role: "assistant",
            content: "👋 Hello! I'm Maria, your Quality Copilot. I can help you with:\n• Analyzing requirement clarity and testability\n• Generating comprehensive test cases\n• Assessing release readiness\n• Providing QA insights and recommendations\n\nWhat would you like help with today?",
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const { toast } = useToast();

    const handleSendMessage = async () => {
        if (!input.trim()) return;

        // Add user message
        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content: input,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setLoading(true);

        try {
            // Parse user intent to route to appropriate copilot feature
            const lowerInput = input.toLowerCase();

            let assistantResponse = "";

            if (
                lowerInput.includes("require") ||
                lowerInput.includes("clarity") ||
                lowerInput.includes("ambiguous")
            ) {
                assistantResponse =
                    "📋 To analyze a requirement's clarity, navigate to the **Requirements** page and click the sparkles icon (✨) on any requirement. I'll analyze it for:\n• Clarity score (0-100)\n• Testability\n• Ambiguous terms\n• Missing criteria\n• Improvement suggestions";
            } else if (
                lowerInput.includes("test") ||
                lowerInput.includes("case") ||
                lowerInput.includes("generate")
            ) {
                assistantResponse =
                    "🧪 To generate test cases, go to the **Requirements** page and click the test tube icon (🧪) on any requirement. I'll create:\n• Positive test cases\n• Negative test cases\n• Edge cases\n• Performance tests\n• Security tests\n\nEach with detailed steps and expected results.";
            } else if (
                lowerInput.includes("release") ||
                lowerInput.includes("ready") ||
                lowerInput.includes("go/no-go")
            ) {
                assistantResponse =
                    "🚀 To check release readiness, navigate to the **Releases** page and click the sparkles icon (✨) on any release. I'll assess:\n• Risk score based on critical defects\n• Go/No-Go decision\n• Blocking issues\n• Release summary";
            } else {
                assistantResponse =
                    "I can help with QA intelligence features:\n\n1️⃣ **Requirement Analysis** - Click sparkles on Requirements page\n2️⃣ **Test Case Generation** - Click test tube on Requirements page\n3️⃣ **Release Readiness** - Click sparkles on Releases page\n\nWhich feature would you like to use?";
            }

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: assistantResponse,
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to process your message",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">
                            <Sparkles className="h-8 w-8 text-accent" />
                            Quality Copilot
                        </h1>
                        <p className="text-muted-foreground mt-2">
                            AI-powered QA intelligence assistant
                        </p>
                    </div>
                    <Badge className="bg-accent text-accent-foreground">Beta</Badge>
                </div>

                <div className="grid gap-6 lg:grid-cols-3">
                    {/* Features */}
                    <div className="lg:col-span-1 space-y-4">
                        <Card>
                            <CardHeader className="pb-3">
                                <CardTitle className="text-base">Quick Actions</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                <Button variant="outline" className="w-full justify-start" disabled>
                                    <Brain className="h-4 w-4 mr-2" />
                                    Analyze Requirements
                                </Button>
                                <Button variant="outline" className="w-full justify-start" disabled>
                                    <Zap className="h-4 w-4 mr-2" />
                                    Generate Tests
                                </Button>
                                <Button variant="outline" className="w-full justify-start" disabled>
                                    <Sparkles className="h-4 w-4 mr-2" />
                                    Check Release Status
                                </Button>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader className="pb-3">
                                <CardTitle className="text-base flex items-center gap-2">
                                    <History className="h-4 w-4" />
                                    Recent
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-sm text-muted-foreground">
                                    No recent analyses yet. Start by asking a question or navigate to the
                                    appropriate page to use copilot features.
                                </p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Chat */}
                    <div className="lg:col-span-2">
                        <Card className="flex flex-col h-[600px]">
                            <CardHeader className="border-b">
                                <CardTitle>Chat with Copilot</CardTitle>
                                <CardDescription>
                                    Ask me about requirements, tests, releases, or QA features
                                </CardDescription>
                            </CardHeader>

                            {/* Messages */}
                            <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                                {messages.map((message) => (
                                    <div
                                        key={message.id}
                                        className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                                    >
                                        <div
                                            className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${message.role === "user"
                                                ? "bg-accent text-accent-foreground"
                                                : "bg-muted text-muted-foreground"
                                                }`}
                                        >
                                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                                            <p
                                                className={`text-xs mt-1 ${message.role === "user"
                                                    ? "text-accent-foreground/70"
                                                    : "text-muted-foreground/70"
                                                    }`}
                                            >
                                                {message.timestamp.toLocaleTimeString([], {
                                                    hour: "2-digit",
                                                    minute: "2-digit",
                                                })}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                                {loading && (
                                    <div className="flex justify-start">
                                        <div className="bg-muted text-muted-foreground px-4 py-2 rounded-lg">
                                            <div className="flex gap-1">
                                                <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce"></div>
                                                <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce delay-100"></div>
                                                <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce delay-200"></div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </CardContent>

                            {/* Input */}
                            <div className="border-t p-4 space-y-3">
                                <Textarea
                                    placeholder="Ask me about requirements, tests, releases, or QA features..."
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter" && e.ctrlKey) {
                                            handleSendMessage();
                                        }
                                    }}
                                    className="resize-none"
                                    rows={3}
                                />
                                <div className="flex justify-between items-center">
                                    <p className="text-xs text-muted-foreground">
                                        Press Ctrl+Enter to send
                                    </p>
                                    <Button
                                        onClick={handleSendMessage}
                                        disabled={!input.trim() || loading}
                                        size="sm"
                                    >
                                        <Send className="h-4 w-4 mr-2" />
                                        Send
                                    </Button>
                                </div>
                            </div>
                        </Card>
                    </div>
                </div>

                {/* Info Cards */}
                <div className="grid gap-4 md:grid-cols-3">
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-base flex items-center gap-2">
                                <Brain className="h-5 w-5 text-accent" />
                                Requirement Analysis
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-muted-foreground">
                                Go to Requirements page and click the sparkles icon to analyze clarity,
                                testability, and identify ambiguous terms.
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-base flex items-center gap-2">
                                <Zap className="h-5 w-5 text-accent" />
                                Test Case Generation
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-muted-foreground">
                                Go to Requirements page and click the test tube icon to automatically
                                generate comprehensive test cases.
                            </p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-base flex items-center gap-2">
                                <Sparkles className="h-5 w-5 text-accent" />
                                Release Readiness
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-muted-foreground">
                                Go to Releases page and click the sparkles icon to assess release
                                readiness and identify blocking issues.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </DashboardLayout>
    );
}
