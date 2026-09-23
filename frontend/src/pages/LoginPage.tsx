import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { BrandMark } from "../components/BrandMark";
import { Field } from "../components/Field";
import { useAuth } from "../hooks/useAuth";
import { useTitle } from "../hooks/useTitle";
import { ApiError } from "../services/api";
import { fieldError, type FieldErrors } from "../services/errors";

export function LoginPage() {
  useTitle("Sign in");
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [detail, setDetail] = useState("");
  const [pending, setPending] = useState(false);
  const demoEmail = import.meta.env.VITE_DEMO_EMAIL;
  const demoPassword = import.meta.env.VITE_DEMO_PASSWORD;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setDetail("");
    setErrors({});
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors(err.errors);
        setDetail(err.detail);
      } else {
        setDetail("Could not reach Orbit.");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="auth-screen">
      <section className="auth-story">
        <div className="auth-story-top">
          <BrandMark tone="paper" size={36} />
          <span>Orbit</span>
        </div>
        <div className="orbit-stage" aria-hidden="true">
          <span className="orbit-ring ring-a" />
          <span className="orbit-ring ring-b" />
          <span className="orbit-core" />
        </div>
        <div className="auth-story-copy">
          <p className="eyebrow light">Autonomous software development</p>
          <h1>Each product keeps its own orbit.</h1>
          <p>
            Orbit is the platform that will specify, plan, and implement software products. It is not itself a workforce
            system, clinic app, or store.
          </p>
          <ul>
            <li>Organizations are isolated.</li>
            <li>A project starts as a description, not invented progress.</li>
            <li>Later agents will work on branches, never directly on main.</li>
          </ul>
        </div>
      </section>
      <section className="auth-form-wrap">
        <form className="auth-form" onSubmit={submit}>
          <div className="mobile-brand">
            <BrandMark />
            <strong>Orbit</strong>
          </div>
          <h2>Sign in</h2>
          <p className="lede">Use the workspace account for your organization.</p>
          <Field label="Email" error={fieldError(errors, "email")}>
            <input
              className="input"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </Field>
          <Field label="Password" error={fieldError(errors, "password")}>
            <input
              className="input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </Field>
          {detail ? <p className="banner is-danger">{detail}</p> : null}
          <button type="submit" className="btn btn-primary btn-block" disabled={pending}>
            {pending ? "Signing in" : "Sign in"}
          </button>
          <p className="form-foot">
            No account yet? <Link to="/register">Create a workspace</Link>
          </p>
          {demoEmail && demoPassword ? (
            <div className="demo-card">
              <strong>Local demo</strong>
              <p>
                {demoEmail}
                <br />
                {demoPassword}
              </p>
              <button
                type="button"
                className="btn btn-ghost btn-small"
                onClick={() => {
                  setEmail(demoEmail);
                  setPassword(demoPassword);
                }}
              >
                Use demo workspace
              </button>
              <small>Available after `python manage.py seed_demo`. Not a production credential.</small>
            </div>
          ) : null}
        </form>
      </section>
    </div>
  );
}
