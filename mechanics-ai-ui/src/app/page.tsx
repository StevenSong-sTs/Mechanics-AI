"use client";
import { useState } from "react";
import Image from "next/image";
import { MessageCircleCode } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import ReactMarkdown from 'react-markdown';

interface Message {
  sender: string;
  text: string;
  sources?: string[];
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "User", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:5000/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: input }),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.json();
      const botMessage = { 
        sender: "Chatbot", 
        text: data.answer,
        sources: data.sources
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error fetching chatbot response:", error);
      const errorMessage = { sender: "Chatbot", text: "Sorry, something went wrong." };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setInput("");
  };

  return (
    <div className="flex h-screen flex-col items-center bg-slate-900 w-full">
      <div className="w-[60%] flex flex-col h-full">
        {/* Header */}
        <div className="flex justify-between items-center border-b border-slate-800 px-4 py-4">
          <div className="w-24"></div>
          <div className="flex items-center gap-2">
            <Image src="/logo.png" alt="Logo" width={80} height={80} />
            <h1 className="text-2xl font-bold text-slate-300">Mechanics AI</h1>
          </div>
          <div className="w-24">
            <Button 
              variant="outline" 
              onClick={handleNewChat}
              className="flex bg-slate-700 text-white border-slate-600 items-center gap-2 transition-all duration-200 hover:bg-slate-600 hover:border-slate-500"
            >
              <MessageCircleCode 
                style={{ width: '24px', height: '24px' }}
              />
              <span className="font-bold">New Chat</span>
            </Button>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full p-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`mb-4 flex ${
                  msg.sender === "User" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`rounded-lg p-3 ${
                    msg.sender === "User"
                      ? "bg-slate-800 text-primary-foreground"
                      : "bg-transparent text-white"
                  }`}
                >
                  {msg.sender === "User" ? (
                    <p className="max-w-[80ch]">{msg.text}</p>
                  ) : (
                    <div>
                      <ReactMarkdown 
                        className="max-w-[80ch] prose prose-invert prose-pre:bg-slate-800 prose-pre:p-2 prose-pre:rounded-md"
                      >
                        {msg.text}
                      </ReactMarkdown>
                      
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-4 border-t border-slate-700 pt-4">
                          <p className="text-sm text-slate-400 mb-2">Sources:</p>
                          <div className="space-y-2">
                            {msg.sources.map((source, idx) => (
                              <div 
                                key={idx} 
                                className="text-sm bg-slate-800 p-2 rounded-md text-slate-300"
                              >
                                {source}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="mb-4 flex justify-start">
                <div className="rounded-lg bg-muted p-3">
                  <p>Typing...</p>
                </div>
              </div>
            )}
          </ScrollArea>
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-800 p-4">
          <div className="flex gap-2">
            <Input
              className="flex-1 text-slate-200 bg-slate-800 border-slate-700 min-h-[60px]"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <Button 
              onClick={handleSend} 
              disabled={isLoading}
              className="bg-slate-600 hover:bg-primary/90 text-white self-center"
            >
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
