import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Field } from "../components/Field";
import { startingPoints } from "../features/projects/examples";
import { useOrganization } from "../hooks/useOrganization";
import { useTitle } from "../hooks/useTitle";
import { api, ApiError } from "../services/api";
import { fieldError, type FieldErrors } from "../services/errors";
import type { Project } from "../types";

export function ProjectCreatePage() {
  useTitle("New project");
  const { organization } = useOrganization();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [summary, setSummary] = useState("");
  const [description, setDescription] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [detail, setDetail] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!organization) return;
    setPending(true);
    setDetail("");
    setErrors({});
    try {
      const project = await api<Project>("/projects/", {
        method: "POST",
        body: JSON.stringify({
          organization: organization.id,
          name,
          summary,
          product_description: description,
        }),
      });
      navigate(`/projects/${project.id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors(err.errors);
        setDetail(Object.keys(err.errors).length ? "The project was not created." : err.detail);
      } else {
        setDetail("Could not reach Orbit.");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="page narrow">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            <Link to="/projects">Projects</Link> / New
          </p>
          <h1>Register a product</h1>
          <p className="lede">
            {organization
              ? `This project will belong to ${organization.name}. Orbit stores the description and holds the lifecycle at Created.`
              : "Create an organization before registering a product."}
          </p>
        </div>
      </header>

      <form className="panel stack" onSubmit={submit}>
        <Field label="Project name" error={fieldError(errors, "name")}>
          <input className="input" value={name} onChange={(event) => setName(event.target.value)} required minLength={2} />
        </Field>
        <Field label="Summary" hint="Optional. One line for lists." error={fieldError(errors, "summary")}>
          <input className="input" value={summary} maxLength={280} onChange={(event) => setSummary(event.target.value)} />
        </Field>
        <Field
          label="Product description"
          hint="Who is it for, and what must it do? This is the source text for later discovery. Orbit will not invent the missing requirements."
          error={fieldError(errors, "product_description")}
        >
          <textarea
            className="textarea"
            rows={8}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            required
            minLength={20}
            placeholder="Describe the product in plain language. Do not describe Orbit itself."
          />
        </Field>
        <div className="examples">
          <span>Starting points, not products Orbit has built</span>
          <div className="example-row">
            {startingPoints.map((example) => (
              <button
                key={example.id}
                type="button"
                className="chip"
                onClick={() => {
                  setName(example.name);
                  setSummary(example.summary);
                  setDescription(example.description);
                }}
              >
                {example.name}
              </button>
            ))}
          </div>
        </div>
        {detail ? <p className="banner is-danger">{detail}</p> : null}
        <div className="row-actions">
          <Link className="btn btn-ghost" to="/projects">
            Cancel
          </Link>
          <button type="submit" className="btn btn-primary" disabled={pending || !organization}>
            {pending ? "Registering" : "Create project"}
          </button>
        </div>
      </form>
    </section>
  );
}
