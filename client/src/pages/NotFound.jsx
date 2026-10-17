import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section className="card">
      <h1>Page not found</h1>
      <p className="muted">That page doesn&apos;t exist.</p>
      <Link to="/">Go home</Link>
    </section>
  )
}
