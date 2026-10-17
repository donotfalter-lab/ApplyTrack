import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api'
import ApplicationCard from '../components/ApplicationCard.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import { STATUSES } from '../constants'

function statusSummary(applications) {
  return STATUSES.map((status) => [status, applications.filter((a) => a.status === status).length])
    .filter(([, count]) => count > 0)
    .map(([status, count]) => `${count} ${status}`)
    .join(', ')
}

export default function Dashboard() {
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let ignore = false
    apiFetch('/applications')
      .then((data) => {
        if (!ignore) setApplications(data)
      })
      .catch((err) => {
        if (!ignore) setError(err.message)
      })
      .finally(() => {
        if (!ignore) setLoading(false)
      })
    return () => {
      ignore = true
    }
  }, [])

  if (loading) return <p className="loading">Loading applications…</p>

  return (
    <section>
      <div className="page-header">
        <div>
          <h1>Your Applications</h1>
          {applications.length > 0 && (
            <p className="muted status-summary">{statusSummary(applications)}</p>
          )}
        </div>
        {applications.length > 0 && (
          <Link to="/applications/new" className="button">
            New Application
          </Link>
        )}
      </div>

      <ErrorMessage message={error} />

      {!error && applications.length === 0 && (
        <div className="card empty-state">
          <p>You haven&apos;t added any applications yet.</p>
          <Link to="/applications/new" className="button">
            Add your first application
          </Link>
        </div>
      )}

      <div className="application-grid">
        {applications.map((application) => (
          <ApplicationCard key={application.id} application={application} />
        ))}
      </div>
    </section>
  )
}
