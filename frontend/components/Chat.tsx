"use client"

import { useState } from "react"
import { sendMessage } from "@/lib/websocket"
import { useRoomStore } from "@/store/roomStore"

interface ChatProps {
  roomCode: string
}

export default function Chat({ roomCode }: ChatProps) {
  void roomCode
  const messages = useRoomStore((s) => s.messages)
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
      <div className="flex-1 overflow-y-auto space-y-1">
        {messages.map((msg, i) => (
          <div key={i} className="text-sm">
            <span className="font-semibold">{msg.user}:</span>{" "}
            {msg.message}
          </div>
        ))}
      </div>

      <div className="flex gap-2 pt-2">
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          className="border border-zinc-700 bg-zinc-950 text-zinc-100 rounded p-2 flex-1"
        />
        <button
          onClick={send}
          className="bg-blue-600 text-white px-4 rounded"
        >
          Send
        </button>
      </div>
    </div>
  )
}
