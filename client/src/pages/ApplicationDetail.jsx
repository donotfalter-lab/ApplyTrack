import { useParams } from 'react-router-dom'

export default function ApplicationDetail() {
  const { id } = useParams()
  return (
    <section className="card">
      <h1>Application Detail</h1>
      <p className="muted">Details for application {id} will go here.</p>
    </section>
  )
}
