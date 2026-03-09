"use client"

import { useState } from "react"
import { sendMessage } from "@/lib/websocket"

interface ChatProps {
  roomCode: string
}

export default function Chat({ roomCode }: ChatProps) {
  // roomCode will be used when chat history is loaded from Zustand state
  void roomCode
  const [message, setMessage] = useState("")

  const send = () => {
    const trimmed = message.trim()
    if (!trimmed) return

    sendMessage({ type: "CHAT_MESSAGE", message: trimmed })
    setMessage("")
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") send()
  }

  return (
    <div className="p-4 flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {/* chat messages rendered here once Zustand state is wired */}
      </div>

      <div className="flex gap-2">
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          className="border p-2 flex-1"
        />
        <button
          onClick={send}
          className="bg-blue-500 text-white px-4"
        >
          Send
        </button>
      </div>
    </div>
  )
}
