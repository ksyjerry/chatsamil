"use client";

import { Button } from "@/components/ui/button";
import {
  PlusCircle,
  MessageSquare,
  Settings,
  User,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useMobile } from "@/hooks/use-mobile";
import { useTheme } from "next-themes";
import Image from "next/image";
import { useEffect, useState } from "react";

interface SidebarProps {
  onClose: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export function Sidebar({
  onClose,
  collapsed,
  onToggleCollapse,
}: SidebarProps) {
  const isMobile = useMobile();
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // useEffect only runs on the client, so now we can safely show the UI
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="h-full flex flex-col bg-gray-100">
        {/* Loading placeholder */}
      </div>
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <div
      className={`h-full flex flex-col ${
        isDark ? "bg-black text-white" : "bg-gray-100 text-gray-700"
      }`}
    >
      <div className="p-3 flex justify-between items-center">
        {!collapsed && (
          <>
            <div className="flex items-center gap-2">
              <div className="relative h-14 w-14">
                <Image
                  src={isDark ? "/pwc_logo_dark.png" : "/pwc_logo_light.png"}
                  alt="PwC Logo"
                  fill
                  className="object-contain"
                />
              </div>
              <h1 className="text-xl font-semibold">Chat Samil</h1>
            </div>
            {!isMobile && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onToggleCollapse}
                className={`h-8 w-8 ${
                  isDark
                    ? "text-white hover:bg-zinc-800"
                    : "text-gray-700 hover:bg-gray-200"
                }`}
              >
                <ChevronLeft size={16} />
                <span className="sr-only">Collapse sidebar</span>
              </Button>
            )}
          </>
        )}

        {collapsed && !isMobile && (
          <div className="mx-auto">
            <div className="relative h-14 w-14">
              <Image
                src={isDark ? "/pwc_logo_dark.png" : "/pwc_logo_light.png"}
                alt="PwC Logo"
                fill
                className="object-contain"
              />
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggleCollapse}
              className={`mt-2 h-8 w-8 ${
                isDark
                  ? "text-white hover:bg-zinc-800"
                  : "text-gray-700 hover:bg-gray-200"
              }`}
            >
              <ChevronRight size={16} />
              <span className="sr-only">Expand sidebar</span>
            </Button>
          </div>
        )}

        {isMobile && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className={`ml-auto h-8 w-8 ${
              isDark
                ? "text-white hover:bg-zinc-800"
                : "text-gray-700 hover:bg-gray-200"
            }`}
          >
            <span className="sr-only">Close sidebar</span>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="lucide lucide-x"
            >
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
          </Button>
        )}
      </div>

      {!collapsed && (
        <>
          <div className="p-3">
            <Button
              className={`w-full justify-start gap-2 ${
                isDark
                  ? "bg-zinc-800 text-white hover:bg-zinc-700 border-zinc-700"
                  : "bg-white text-gray-700 hover:bg-gray-50 border-gray-200"
              }`}
              variant="outline"
            >
              <PlusCircle size={16} />
              New Chat
            </Button>
          </div>

          <div className="flex-1 overflow-auto p-3">
            <div className="space-y-2">
              <h2
                className={`text-xs font-semibold uppercase tracking-wider mb-2 ${
                  isDark ? "text-zinc-400" : "text-gray-500"
                }`}
              >
                Recent Chats
              </h2>
              {[1, 2, 3, 4, 5].map((i) => (
                <Button
                  key={i}
                  variant="ghost"
                  className={`w-full justify-start gap-2 ${
                    isDark
                      ? "text-white hover:bg-zinc-800"
                      : "text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  <MessageSquare size={16} />
                  Chat {i}
                </Button>
              ))}
            </div>
          </div>

          <div
            className={`p-3 border-t ${
              isDark ? "border-zinc-800" : "border-gray-200"
            }`}
          >
            <div className="space-y-2">
              <Button
                variant="ghost"
                className={`w-full justify-start gap-2 ${
                  isDark
                    ? "text-white hover:bg-zinc-800"
                    : "text-gray-700 hover:bg-gray-200"
                }`}
              >
                <User size={16} />
                Profile
              </Button>
              <Button
                variant="ghost"
                className={`w-full justify-start gap-2 ${
                  isDark
                    ? "text-white hover:bg-zinc-800"
                    : "text-gray-700 hover:bg-gray-200"
                }`}
              >
                <Settings size={16} />
                Settings
              </Button>
              <Button
                variant="ghost"
                className="w-full justify-start gap-2 text-red-500"
              >
                <LogOut size={16} />
                Logout
              </Button>
            </div>
          </div>
        </>
      )}

      {collapsed && !isMobile && (
        <>
          <div className="p-3 mt-2">
            <Button
              className={`w-full justify-center ${
                isDark
                  ? "bg-zinc-800 text-white hover:bg-zinc-700 border-zinc-700"
                  : "bg-white text-gray-700 hover:bg-gray-50 border-gray-200"
              }`}
              variant="outline"
              size="icon"
            >
              <PlusCircle size={16} />
              <span className="sr-only">New Chat</span>
            </Button>
          </div>

          <div className="flex-1 overflow-auto p-3">
            <div className="space-y-3 flex flex-col items-center">
              {[1, 2, 3, 4, 5].map((i) => (
                <Button
                  key={i}
                  variant="ghost"
                  size="icon"
                  className={`h-9 w-9 ${
                    isDark
                      ? "text-white hover:bg-zinc-800"
                      : "text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  <MessageSquare size={16} />
                  <span className="sr-only">Chat {i}</span>
                </Button>
              ))}
            </div>
          </div>

          <div
            className={`p-3 border-t ${
              isDark ? "border-zinc-800" : "border-gray-200"
            } flex flex-col items-center space-y-3`}
          >
            <Button
              variant="ghost"
              size="icon"
              className={`h-9 w-9 ${
                isDark
                  ? "text-white hover:bg-zinc-800"
                  : "text-gray-700 hover:bg-gray-200"
              }`}
            >
              <User size={16} />
              <span className="sr-only">Profile</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className={`h-9 w-9 ${
                isDark
                  ? "text-white hover:bg-zinc-800"
                  : "text-gray-700 hover:bg-gray-200"
              }`}
            >
              <Settings size={16} />
              <span className="sr-only">Settings</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 text-red-500"
            >
              <LogOut size={16} />
              <span className="sr-only">Logout</span>
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
