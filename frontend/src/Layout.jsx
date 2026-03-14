import { Outlet, useParams, Link, NavLink } from "react-router-dom";

const HeartIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
  </svg>
);

export default function Layout() {
  const { patientId } = useParams();
  return (
    <>
      <header className="app-header">
        <Link to="/" className="header-brand" aria-label="DailyCare home">
          <span className="header-heart" style={{ color: "rgba(255,255,255,0.95)" }}>
            <HeartIcon />
          </span>
          <span className="header-title">DailyCare</span>
        </Link>
        {patientId && (
          <a
            href="tel:911"
            className="btn btn-sos"
            style={{ textDecoration: "none", flexShrink: 0 }}
            aria-label="Emergency: call for help"
          >
            SOS
          </a>
        )}
      </header>
      {patientId && (
        <nav className="app-nav">
          <NavLink to={`/patient/${patientId}`} end>Home</NavLink>
          <NavLink to={`/patient/${patientId}/medications`}>Medications</NavLink>
          <NavLink to={`/patient/${patientId}/symptoms`}>Symptoms</NavLink>
          <NavLink to={`/patient/${patientId}/vitals`}>Vitals</NavLink>
          <NavLink to={`/patient/${patientId}/export`}>Export</NavLink>
          <NavLink to={`/patient/${patientId}/recommendations`}>Chat</NavLink>
        </nav>
      )}
      <main>
        <Outlet />
      </main>
    </>
  );
}
