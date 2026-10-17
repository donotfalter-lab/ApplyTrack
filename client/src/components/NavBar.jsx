import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function NavBar() {
  const { user, loading, logout } = useAuth()

  return (
    <header className="navbar">
      <nav className="navbar-inner">
        <Link to="/" className="brand">ApplyTrack</Link>

        {!loading && user && (
          <>
            <div className="nav-links">
              <NavLink to="/" end>Dashboard</NavLink>
              <NavLink to="/applications/new">New Application</NavLink>
            </div>
            <div className="nav-user">
              <span className="username">{user.username}</span>
              <button type="button" className="button button-secondary" onClick={logout}>
                Logout
              </button>
            </div>
          </>
        )}

        {!loading && !user && (
          <div className="nav-links">
            <NavLink to="/login">Login</NavLink>
            <NavLink to="/signup">Sign Up</NavLink>
          </div>
        )}
      </nav>
    </header>
  )
}
