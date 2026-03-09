import { useRoomStore } from "@/store/roomStore"

interface ParticipantsProps {
  roomCode: string
}

export default function Participants({ roomCode: _ }: ParticipantsProps) {
  const participants = useRoomStore((s) => s.participants)
  const host = useRoomStore((s) => s.host)

  return (
    <div className="p-4 h-full overflow-y-auto">
      <h2 className="font-bold mb-2">Participants</h2>
      {participants.length === 0 ? (
        <p className="text-sm text-gray-400">No participants yet</p>
      ) : (
        participants.map((p) => (
          <div key={p} className="py-1 text-sm">
            {p}{p === host ? " (host)" : ""}
          </div>
        ))
      )}
    </div>
  )
}
