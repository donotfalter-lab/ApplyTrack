import { useParams } from 'react-router-dom'

export default function ApplicationForm() {
  const { id } = useParams()
  return (
    <section className="card">
      <h1>{id ? 'Edit Application' : 'New Application'}</h1>
      <p className="muted">The application form will go here.</p>
    </section>
  )
}
