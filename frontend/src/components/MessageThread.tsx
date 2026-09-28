import { useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import { getThread, MessageOut, sendMessage } from '../lib/api'
import { useAuth } from '../lib/auth'

export default function MessageThread({ otherUserId, otherName }: { otherUserId: number; otherName: string }) {
  const { user } = useAuth()
  const [messages, setMessages] = useState<MessageOut[]>([])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  async function load() {
    const thread = await getThread(otherUserId)
    setMessages(thread)
  }

  useEffect(() => {
    load()
  }, [otherUserId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    if (!draft.trim()) return
    setSending(true)
    try {
      await sendMessage(otherUserId, draft.trim())
      setDraft('')
      await load()
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="card flex flex-col h-96">
      <div className="data-label pb-3 border-b border-border mb-3">Conversation with {otherName}</div>
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {messages.length === 0 && (
          <p className="text-sm text-muted">No messages yet. Start the conversation below.</p>
        )}
        {messages.map((m) => {
          const mine = m.sender_id === user?.id
          return (
            <div key={m.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[75%] px-3 py-2 rounded-sm text-sm ${
                  mine ? 'bg-teal text-paper' : 'bg-teal-light text-ink'
                }`}
              >
                <p>{m.body}</p>
                <p className={`text-[11px] mt-1 ${mine ? 'text-paper/70' : 'text-muted'}`}>
                  {new Date(m.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={handleSend} className="flex gap-2 mt-3 pt-3 border-t border-border">
        <input
          className="field-input"
          placeholder="Write a message…"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        <button type="submit" disabled={sending} className="btn-primary px-3">
          <Send size={15} />
        </button>
      </form>
    </div>
  )
}
