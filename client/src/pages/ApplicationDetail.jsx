import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { apiFetch } from '../api'
import ErrorMessage from '../components/ErrorMessage.jsx'
import ResponseGenerator from '../components/ResponseGenerator.jsx'
import ResponseList from '../components/ResponseList.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { STATUSES } from '../constants'

export default function ApplicationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [application, setApplication] = useState(null)
  const [responses, setResponses] = useState([])
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [error, setError] = useState('')
  const [statusSaving, setStatusSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let ignore = false
    apiFetch(`/applications/${id}`)
      .then((data) => {
        if (ignore) return
        const { responses: saved, ...details } = data
        setApplication(details)
        setResponses(saved)
      })
      .catch((err) => {
        if (ignore) return
        if (err.status === 404) setNotFound(true)
        else setError(err.message)
      })
      .finally(() => {
        if (!ignore) setLoading(false)
      })
    return () => {
      ignore = true
    }
  }, [id])

  async function handleStatusChange(event) {
    const previous = application.status
    const status = event.target.value
    setError('')
    setApplication((current) => ({ ...current, status }))
    setStatusSaving(true)
    try {
      const updated = await apiFetch(`/applications/${id}`, { method: 'PATCH', body: { status } })
      setApplication(updated)
    } catch (err) {
      setApplication((current) => ({ ...current, status: previous }))
      setError(`Couldn't update status: ${err.message}`)
    } finally {
      setStatusSaving(false)
    }
  }

  async function handleDelete() {
    const confirmed = window.confirm(
      `Delete your application to ${application.company}? This also deletes its saved responses.`,
    )
    if (!confirmed) return
    setError('')
    setDeleting(true)
    try {
      await apiFetch(`/applications/${id}`, { method: 'DELETE' })
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message)
      setDeleting(false)
    }
  }

  if (loading) return <p className="loading">Loading application…</p>

  if (notFound) {
    return (
      <section className="card">
        <h1>Application not found</h1>
        <p className="muted">It may have been deleted, or the link is wrong.</p>
        <Link to="/">Back to dashboard</Link>
      </section>
    )
  }

  if (!application) return <ErrorMessage message={error} />

  return (
    <div className="stack">
      <section className="card">
        <div className="detail-header">
          <div>
            <h1>{application.company}</h1>
            <p className="detail-role">{application.role}</p>
          </div>
          <StatusBadge status={application.status} />
        </div>

        <ErrorMessage message={error} />

        <div className="detail-controls">
          <label htmlFor="status" className="inline-label">
            Status
            <select
              id="status"
              value={application.status}
              onChange={handleStatusChange}
              disabled={statusSaving}
            >
              {STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>
          <div className="button-row">
            <Link to={`/applications/${id}/edit`} className="button button-secondary">
              Edit
            </Link>
            <button
              type="button"
              className="button button-danger"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? 'Deleting…' : 'Delete'}
            </button>
          </div>
        </div>

        <h2 className="section-title">Job description</h2>
        {application.job_description ? (
          <p className="preserve-lines">{application.job_description}</p>
        ) : (
          <p className="muted">No job description added.</p>
        )}
      </section>

      <ResponseGenerator
        applicationId={application.id}
        onCreated={(response) => setResponses((current) => [response, ...current])}
      />

      <ResponseList
        responses={responses}
        onDeleted={(responseId) =>
          setResponses((current) => current.filter((r) => r.id !== responseId))
        }
      />
    </div>
  )
}
