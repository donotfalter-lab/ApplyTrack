import ResponseCard from './ResponseCard.jsx'

export default function ResponseList({ responses, onDeleted }) {
  return (
    <section className="stack">
      <h2 className="section-title">Saved responses</h2>
      {responses.length === 0 ? (
        <p className="card muted">No saved responses yet. Generate your first one above.</p>
      ) : (
        responses.map((response) => (
          <ResponseCard key={response.id} response={response} onDeleted={onDeleted} />
        ))
      )}
    </section>
  )
}
