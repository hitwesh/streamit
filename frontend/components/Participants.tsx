import { useRoomStore } from "@/store/roomStore"

export default function Participants() {
  const participants = useRoomStore((s) => s.participants)
  const host = useRoomStore((s) => s.host)

  return (
    <div className="p-4 h-full overflow-y-auto">
      <h2 className="text-xs uppercase tracking-[0.2em] text-[color:var(--color-muted)]">
        Participants
      </h2>
      {participants.length === 0 ? (
        <p className="mt-3 text-sm text-[color:var(--color-muted)]">
          No participants yet
        </p>
      ) : (
        <div className="mt-4 space-y-2">
          {participants.map((p) => (
            <div
              key={p}
              className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm"
            >
              <span>{p}</span>
              {p === host ? <span className="badge">Host</span> : null}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
