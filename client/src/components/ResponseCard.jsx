import { useEffect, useRef, useState } from 'react'
import { apiFetch } from '../api'
import ErrorMessage from './ErrorMessage.jsx'

// The backend stores UTC times without a timezone suffix.
function formatDate(isoString) {
  const hasZone = /[zZ]|[+-]\d\d:\d\d$/.test(isoString)
  const date = new Date(hasZone ? isoString : `${isoString}Z`)
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  const ok = document.execCommand('copy')
  textarea.remove()
  if (!ok) throw new Error('Copy failed')
}

export default function ResponseCard({ response, onDeleted }) {
  const [copyLabel, setCopyLabel] = useState('Copy')
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')
  const resetTimer = useRef(null)

  useEffect(() => () => clearTimeout(resetTimer.current), [])

  async function handleCopy() {
    try {
      await copyText(response.generated_text)
      setCopyLabel('Copied')
    } catch {
      setCopyLabel('Copy failed')
    }
    clearTimeout(resetTimer.current)
    resetTimer.current = setTimeout(() => setCopyLabel('Copy'), 2000)
  }

  async function handleDelete() {
    if (!window.confirm('Delete this saved response?')) return
    setError('')
    setDeleting(true)
    try {
      await apiFetch(`/responses/${response.id}`, { method: 'DELETE' })
      onDeleted(response.id)
    } catch (err) {
      setError(err.message)
      setDeleting(false)
    }
  }

  return (
    <article className="card response-card">
      <p className="response-question">{response.prompt}</p>
      <p className="preserve-lines">{response.generated_text}</p>
      <ErrorMessage message={error} />
      <div className="response-footer">
        <time className="muted" dateTime={response.created_at}>
          {formatDate(response.created_at)}
        </time>
        <div className="button-row">
          <button type="button" className="button button-secondary button-small" onClick={handleCopy}>
            {copyLabel}
          </button>
          <button
            type="button"
            className="button button-danger button-small"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>
    </article>
  )
}
