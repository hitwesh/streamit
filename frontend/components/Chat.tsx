"use client"

import { useMemo, useState } from "react"
import { sendMessage } from "@/lib/websocket"
import { useRoomStore } from "@/store/roomStore"

export default function Chat({
  isDisabled = false,
}: {
  isDisabled?: boolean
}) {
  const messages = useRoomStore((s) => s.messages)
  const [message, setMessage] = useState("")
  const formatter = useMemo(
    () =>
      new Intl.DateTimeFormat("en", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    []
  )

  const send = () => {
    const trimmed = message.trim()
    if (!trimmed || isDisabled) return

    sendMessage({ type: "CHAT_MESSAGE", message: trimmed })
    setMessage("")
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") send()
  }

  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <div className="flex-1 space-y-3 overflow-y-auto pr-2">
        {messages.length === 0 ? (
          <p className="text-sm text-[color:var(--color-muted)]">
            No messages yet.
          </p>
        ) : (
          messages.map((msg, i) => {
            const parsed = Date.parse(msg.created_at)
            const time = Number.isNaN(parsed)
              ? ""
              : formatter.format(new Date(parsed))

            return (
              <div key={i} className="rounded-2xl border border-black/5 bg-white/70 px-3 py-2">
                <div className="flex items-baseline justify-between text-xs text-[color:var(--color-muted)]">
                  <span className="font-medium text-[color:var(--color-foreground)]">
                    {msg.user}
                  </span>
                  <span>{time}</span>
                </div>
                <p className="text-sm text-[color:var(--color-foreground)]">
                  {msg.message}
                </p>
              </div>
            )
          })
        )}
      </div>

      <div className="flex gap-2">
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isDisabled ? "Chat disabled" : "Type a message"}
          disabled={isDisabled}
          className="input flex-1"
        />
        <button onClick={send} disabled={isDisabled} className="btn btn-primary">
          Send
        </button>
      </div>
    </div>
  )
}
