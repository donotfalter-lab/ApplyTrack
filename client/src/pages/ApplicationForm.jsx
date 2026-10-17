import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { apiFetch } from '../api'
import ErrorMessage from '../components/ErrorMessage.jsx'
import { STATUSES } from '../constants'

const EMPTY_FORM = { company: '', role: '', status: 'applied', job_description: '' }

export default function ApplicationForm() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()

  const [form, setForm] = useState(EMPTY_FORM)
  const [fieldErrors, setFieldErrors] = useState({})
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(isEdit)
  const [notFound, setNotFound] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!isEdit) return
    let ignore = false
    apiFetch(`/applications/${id}`)
      .then((app) => {
        if (ignore) return
        setForm({
          company: app.company,
          role: app.role,
          status: app.status,
          job_description: app.job_description || '',
        })
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
  }, [id, isEdit])

  function handleChange(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
    if (fieldErrors[name]) setFieldErrors((current) => ({ ...current, [name]: '' }))
  }

  function validate() {
    const errors = {}
    if (!form.company.trim()) errors.company = 'Company is required'
    if (!form.role.trim()) errors.role = 'Role is required'
    return errors
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    const errors = validate()
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return

    const body = {
      company: form.company.trim(),
      role: form.role.trim(),
      status: form.status,
      job_description: form.job_description.trim() || null,
    }

    setSaving(true)
    try {
      const saved = isEdit
        ? await apiFetch(`/applications/${id}`, { method: 'PATCH', body })
        : await apiFetch('/applications', { method: 'POST', body })
      navigate(`/applications/${saved.id}`)
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  function handleCancel() {
    navigate(isEdit ? `/applications/${id}` : '/')
  }

  if (loading) return <p className="loading">Loading application…</p>

  if (notFound) {
    return (
      <section className="card">
        <h1>Application not found</h1>
        <p className="muted">It may have been deleted.</p>
        <Link to="/">Back to dashboard</Link>
      </section>
    )
  }

  return (
    <form className="card form form-wide" onSubmit={handleSubmit} noValidate>
      <h1>{isEdit ? 'Edit Application' : 'New Application'}</h1>
      <ErrorMessage message={error} />

      <label htmlFor="company">Company *</label>
      <input
        id="company"
        name="company"
        value={form.company}
        onChange={handleChange}
        aria-invalid={Boolean(fieldErrors.company)}
      />
      {fieldErrors.company && <p className="field-error">{fieldErrors.company}</p>}

      <label htmlFor="role">Role *</label>
      <input
        id="role"
        name="role"
        value={form.role}
        onChange={handleChange}
        aria-invalid={Boolean(fieldErrors.role)}
      />
      {fieldErrors.role && <p className="field-error">{fieldErrors.role}</p>}

      <label htmlFor="status">Status</label>
      <select id="status" name="status" value={form.status} onChange={handleChange}>
        {STATUSES.map((status) => (
          <option key={status} value={status}>
            {status}
          </option>
        ))}
      </select>

      <label htmlFor="job_description">Job description</label>
      <textarea
        id="job_description"
        name="job_description"
        rows={8}
        value={form.job_description}
        onChange={handleChange}
        placeholder="Paste the job description to get better AI drafts."
      />

      <div className="form-actions">
        <button type="button" className="button button-secondary" onClick={handleCancel}>
          Cancel
        </button>
        <button type="submit" className="button" disabled={saving}>
          {saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Create Application'}
        </button>
      </div>
    </form>
  )
}
