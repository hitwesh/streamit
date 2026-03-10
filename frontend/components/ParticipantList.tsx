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
    <div className="p-3">
      <h3 className="font-semibold">Participants</h3>
      {participants.length === 0 ? (
        <p className="text-sm text-gray-400">No participants yet</p>
      ) : (
        participants.map((p) => (
          <div key={p.id} className="text-sm">
            {p.display_name} {p.is_host ? "(host)" : ""}
          </div>
        ))
      )}
    </div>
  )
}
