import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { BrandMark } from "../components/BrandMark";
import { Field } from "../components/Field";
import { useAuth } from "../hooks/useAuth";
import { useTitle } from "../hooks/useTitle";
import { ApiError } from "../services/api";
import { fieldError, type FieldErrors } from "../services/errors";

export function RegisterPage() {
  useTitle("Create workspace");
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    organization_name: "",
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [detail, setDetail] = useState("");
  const [pending, setPending] = useState(false);

  function set(name: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setDetail("");
    setErrors({});
    try {
      await register(form);
      navigate("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors(err.errors);
        setDetail(Object.keys(err.errors).length ? "Check the highlighted fields." : err.detail);
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
        <div className="auth-story-copy">
          <p className="eyebrow light">New workspace</p>
          <h1>Start with the tenant, not the product.</h1>
          <p>
            Registration creates your user and an organization you own. Projects you add later belong to that
            organization and are invisible to every other one.
          </p>
        </div>
      </section>
      <section className="auth-form-wrap">
        <form className="auth-form" onSubmit={submit}>
          <div className="mobile-brand">
            <BrandMark />
            <strong>Orbit</strong>
          </div>
          <h2>Create a workspace</h2>
          <div className="split-fields">
            <Field label="First name" error={fieldError(errors, "first_name")}>
              <input className="input" value={form.first_name} onChange={(event) => set("first_name", event.target.value)} required />
            </Field>
            <Field label="Last name" error={fieldError(errors, "last_name")}>
              <input className="input" value={form.last_name} onChange={(event) => set("last_name", event.target.value)} />
            </Field>
          </div>
          <Field label="Email" error={fieldError(errors, "email")}>
            <input
              className="input"
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={(event) => set("email", event.target.value)}
              required
            />
          </Field>
          <Field label="Password" hint="At least 10 characters." error={fieldError(errors, "password")}>
            <input
              className="input"
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={(event) => set("password", event.target.value)}
              required
              minLength={10}
            />
          </Field>
          <Field
            label="Organization name"
            hint="Leave blank to use your first name. You can rename it later."
            error={fieldError(errors, "organization_name")}
          >
            <input
              className="input"
              value={form.organization_name}
              onChange={(event) => set("organization_name", event.target.value)}
            />
          </Field>
          {detail ? <p className="banner is-danger">{detail}</p> : null}
          <button type="submit" className="btn btn-primary btn-block" disabled={pending}>
            {pending ? "Creating" : "Create workspace"}
          </button>
          <p className="form-foot">
            Already registered? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </section>
    </div>
  );
}
