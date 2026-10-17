import { useState } from 'react'
import { apiFetch } from '../api'
import { QUESTION_MAX_LENGTH, QUESTION_MIN_LENGTH } from '../constants'
import ErrorMessage from './ErrorMessage.jsx'

export default function ResponseGenerator({ applicationId, onCreated }) {
  const [question, setQuestion] = useState('')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [failedQuestion, setFailedQuestion] = useState('')

  const length = question.trim().length

  async function generate(text) {
    setError('')
    setFailedQuestion('')
    setGenerating(true)
    try {
      const response = await apiFetch(`/applications/${applicationId}/responses`, {
        method: 'POST',
        body: { question: text },
      })
      onCreated(response)
      setQuestion('')
    } catch (err) {
      setError(err.message)
      setFailedQuestion(text)
    } finally {
      setGenerating(false)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    const text = question.trim()
    if (text.length < QUESTION_MIN_LENGTH || text.length > QUESTION_MAX_LENGTH) {
      setFailedQuestion('')
      setError(
        `Question must be ${QUESTION_MIN_LENGTH} to ${QUESTION_MAX_LENGTH} characters (currently ${text.length}).`,
      )
      return
    }
    generate(text)
  }

  return (
    <section className="card">
      <h2 className="section-title">Draft an answer with AI</h2>
      <form className="form form-full" onSubmit={handleSubmit} noValidate>
        <label htmlFor="question">Screening question</label>
        <textarea
          id="question"
          rows={3}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Why do you want to work here?"
          disabled={generating}
        />
        <p className={`hint ${length > QUESTION_MAX_LENGTH ? 'hint-error' : ''}`}>
          {length} / {QUESTION_MAX_LENGTH} characters
        </p>

        <ErrorMessage message={error} />

        <div className="button-row">
          <button type="submit" className="button" disabled={generating}>
            {generating ? 'Generating...' : 'Generate'}
          </button>
          {failedQuestion && !generating && (
            <button
              type="button"
              className="button button-secondary"
              onClick={() => generate(failedQuestion)}
            >
              Retry
            </button>
          )}
        </div>
      </form>
    </section>
  )
}
