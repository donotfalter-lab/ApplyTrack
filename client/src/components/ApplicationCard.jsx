import { Link } from 'react-router-dom'
import StatusBadge from './StatusBadge.jsx'

export default function ApplicationCard({ application }) {
  return (
    <Link to={`/applications/${application.id}`} className="card application-card">
      <div className="application-card-header">
        <h2>{application.company}</h2>
        <StatusBadge status={application.status} />
      </div>
      <p className="muted">{application.role}</p>
    </Link>
  )
}
