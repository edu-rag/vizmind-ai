'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import {
    ChevronLeft,
    ChevronRight,
    Send,
    MessageCircle,
    Bot,
    User,
    X,
    RotateCcw,
    Sparkles
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { askQuestion } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    sources?: Array<{
        type: string;
        identifier: string;
        title: string;
        snippet: string;
    }>;
}

export function ChatSidebar() {
    const {
        currentMap,
        jwt,
        user,
        isChatSidebarOpen,
        setChatSidebarOpen,
    } = useAppStore();

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isMobile, setIsMobile] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 768);
        };

        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        // Add welcome message when opening chat for the first time
        if (isChatSidebarOpen && messages.length === 0 && currentMap) {
            const welcomeMessage: ChatMessage = {
                id: `welcome-${Date.now()}`,
                role: 'assistant',
                content: `Hello! I'm here to help you explore your concept map "${currentMap.source_filename?.replace('.pdf', '') || 'Document'}". You can ask me questions about any concepts, relationships, or details from your document. What would you like to know?`,
                timestamp: new Date(),
            };
            setMessages([welcomeMessage]);
        }
    }, [isChatSidebarOpen, currentMap, messages.length]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSendMessage = async () => {
        if (!inputValue.trim() || !currentMap || !jwt || isLoading) return;

        const userMessage: ChatMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: inputValue.trim(),
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const result = await askQuestion(
                currentMap.mongodb_doc_id,
                userMessage.content,
                jwt
            );

            if (result.data) {
                const assistantMessage: ChatMessage = {
                    id: `assistant-${Date.now()}`,
                    role: 'assistant',
                    content: result.data.answer,
                    timestamp: new Date(),
                    sources: result.data.cited_sources,
                };
                setMessages(prev => [...prev, assistantMessage]);
            } else {
                const errorMessage: ChatMessage = {
                    id: `error-${Date.now()}`,
                    role: 'assistant',
                    content: "I apologize, but I couldn't generate an answer to your question. Please try rephrasing or asking about a different aspect of the document.",
                    timestamp: new Date(),
                };
                setMessages(prev => [...prev, errorMessage]);
            }
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage: ChatMessage = {
                id: `error-${Date.now()}`,
                role: 'assistant',
                content: "I encountered an error while processing your question. Please try again.",
                timestamp: new Date(),
            };
            setMessages(prev => [...prev, errorMessage]);
            toast.error('Failed to send message');
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const clearChat = () => {
        setMessages([]);
        if (currentMap) {
            const welcomeMessage: ChatMessage = {
                id: `welcome-${Date.now()}`,
                role: 'assistant',
                content: `Hello! I'm here to help you explore your concept map "${currentMap.source_filename?.replace('.pdf', '') || 'Document'}". You can ask me questions about any concepts, relationships, or details from your document. What would you like to know?`,
                timestamp: new Date(),
            };
            setMessages([welcomeMessage]);
        }
    };

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    if (!currentMap) {
        return null;
    }

    return (
        <div
            className={cn(
                'h-full bg-background border-l border-border transition-all duration-300 flex flex-col',
                'shadow-sm',
                isMobile ? 'w-full' : (isChatSidebarOpen ? 'w-80' : 'w-0'),
                !isChatSidebarOpen && 'overflow-hidden'
            )}
        >
            {/* Header */}
            <div className="p-4 border-b border-border bg-background/95 backdrop-blur-sm">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center">
                            <MessageCircle className="h-4 w-4 text-white" />
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-foreground">
                                AI Assistant
                            </h2>
                            <p className="text-xs text-muted-foreground">
                                Ask questions about your map
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center space-x-1">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={clearChat}
                            className="h-8 w-8"
                            title="Clear chat"
                        >
                            <RotateCcw className="h-4 w-4" />
                        </Button>

                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setChatSidebarOpen(false)}
                            className="h-8 w-8"
                            title={isChatSidebarOpen ? 'Close chat' : 'Open chat'}
                        >
                            {isChatSidebarOpen ? (
                                <X className="h-4 w-4" />
                            ) : (
                                <MessageCircle className="h-4 w-4" />
                            )}
                        </Button>
                    </div>
                </div>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={cn(
                                'flex gap-3',
                                message.role === 'user' ? 'justify-end' : 'justify-start'
                            )}
                        >
                            {message.role === 'assistant' && (
                                <div className="w-7 h-7 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                                    <Bot className="h-4 w-4 text-white" />
                                </div>
                            )}

                            <div
                                className={cn(
                                    'max-w-[85%] rounded-lg px-3 py-2 text-sm',
                                    message.role === 'user'
                                        ? 'bg-primary text-primary-foreground ml-auto'
                                        : 'bg-muted text-foreground'
                                )}
                            >
                                <div className="whitespace-pre-wrap break-words">
                                    {message.content}
                                </div>

                                {message.sources && message.sources.length > 0 && (
                                    <div className="mt-2 pt-2 border-t border-border/50">
                                        <p className="text-xs text-muted-foreground mb-1">Sources:</p>
                                        <div className="space-y-1">
                                            {message.sources.map((source, index) => (
                                                <div
                                                    key={index}
                                                    className="text-xs bg-background/50 rounded p-1 border border-border/30"
                                                >
                                                    <p className="font-medium truncate">{source.title}</p>
                                                    <p className="text-muted-foreground truncate">{source.snippet}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <div className="flex justify-end mt-1">
                                    <span className="text-xs opacity-60">
                                        {formatTime(message.timestamp)}
                                    </span>
                                </div>
                            </div>

                            {message.role === 'user' && user && (
                                <Avatar className="w-7 h-7 flex-shrink-0 mt-1">
                                    <AvatarImage src={user.picture} alt={user.name} />
                                    <AvatarFallback className="text-xs">
                                        {user.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                                    </AvatarFallback>
                                </Avatar>
                            )}
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex gap-3 justify-start">
                            <div className="w-7 h-7 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                                <Bot className="h-4 w-4 text-white" />
                            </div>
                            <div className="bg-muted rounded-lg px-3 py-2 max-w-[85%]">
                                <div className="flex items-center space-x-1">
                                    <div className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce" />
                                    <div className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                                    <div className="w-2 h-2 bg-muted-foreground/60 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </ScrollArea>

            {/* Input */}
            <div className="p-4 border-t border-border bg-background">
                <div className="flex gap-2">
                    <Input
                        ref={inputRef}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyPress}
                        placeholder="Ask a question about your concept map..."
                        disabled={isLoading}
                        className="flex-1 text-sm"
                    />
                    <Button
                        onClick={handleSendMessage}
                        disabled={!inputValue.trim() || isLoading}
                        size="icon"
                        className="h-10 w-10 flex-shrink-0"
                    >
                        <Send className="h-4 w-4" />
                    </Button>
                </div>

                <div className="mt-2 flex flex-wrap gap-1">
                    {['What are the main concepts?', 'Explain relationships', 'Summarize key points'].map((suggestion) => (
                        <Button
                            key={suggestion}
                            variant="outline"
                            size="sm"
                            className="h-6 px-2 text-xs"
                            onClick={() => setInputValue(suggestion)}
                            disabled={isLoading}
                        >
                            {suggestion}
                        </Button>
                    ))}
                </div>
            </div>
        </div>
    );
}

// Export a simple chat toggle button that can be used in other components
export function ChatToggleButton({
    isOpen,
    onClick,
    variant = "outline",
    size = "sm",
    showLabel = true,
    className = ""
}: {
    isOpen: boolean;
    onClick: () => void;
    variant?: "outline" | "default" | "ghost";
    size?: "sm" | "icon";
    showLabel?: boolean;
    className?: string;
}) {
    return (
        <Button
            variant={isOpen ? "default" : variant}
            size={size}
            onClick={onClick}
            className={cn("touch-target", className)}
            title={isOpen ? "Close chat" : "Open chat"}
        >
            <MessageCircle className={size === "icon" ? "h-4 w-4" : "mr-2 h-4 w-4"} />
            {showLabel && size !== "icon" && (isOpen ? "Close Chat" : "Chat")}
        </Button>
    );
}
