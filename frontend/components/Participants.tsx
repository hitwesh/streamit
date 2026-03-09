interface ParticipantsProps {
  roomCode: string
}

export default function Participants({ roomCode: _ }: ParticipantsProps) {
  // roomCode will be used when participant list is read from Zustand state
  // Placeholder — will populate from ROOM_PARTICIPANTS / USER_JOINED / USER_LEFT events
  const participants: string[] = []

  return (
    <div className="p-4 h-full overflow-y-auto">
      <h2 className="font-bold mb-2">Participants</h2>
      {participants.length === 0 ? (
        <p className="text-sm text-gray-400">No participants yet</p>
      ) : (
        participants.map((p) => (
          <div key={p} className="py-1 text-sm">{p}</div>
        ))
      )}
    </div>
  )
}
