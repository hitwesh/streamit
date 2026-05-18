"use client"

type Participant = {
  id: string
  display_name: string
  is_host: boolean
}

export default function ParticipantList({
  participants,
}: {
  participants: Participant[]
}) {
  return (
    <div className="p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-[color:var(--color-muted)]">
          Participants
        </h3>
        <span className="text-xs text-[color:var(--color-muted)]">
          {participants.length}
        </span>
      </div>
      {participants.length === 0 ? (
        <p className="mt-3 text-sm text-[color:var(--color-muted)]">
          No participants yet.
        </p>
      ) : (
        <div className="mt-4 space-y-2">
          {participants.map((p) => (
            <div
              key={p.id}
              className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm"
            >
              <span className="text-[color:var(--color-foreground)]">
                {p.display_name}
              </span>
              {p.is_host ? (
                <span className="badge">Host</span>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
