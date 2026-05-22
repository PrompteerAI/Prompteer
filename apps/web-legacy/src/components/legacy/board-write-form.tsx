"use client";

import { useState } from "react";

import { Link } from "@/i18n/navigation";

type BoardWriteFormProps = {
  labels: {
    backBoard: string;
    contentLabel: string;
    contentValue: string;
    draftSaved: string;
    previewTitle: string;
    reset: string;
    submit: string;
    titleLabel: string;
    titleValue: string;
    typeLabel: string;
    typeQuestion: string;
    typeShare: string;
    validationError: string;
  };
};

export function BoardWriteForm({
  labels,
}: BoardWriteFormProps): React.ReactElement {
  const [title, setTitle] = useState(labels.titleValue);
  const [content, setContent] = useState(labels.contentValue);
  const [postType, setPostType] = useState<"question" | "share">("question");
  const [status, setStatus] = useState<"idle" | "saved" | "invalid">("idle");

  return (
    <form
      className="legacy-panel legacy-form-grid"
      onSubmit={(event) => {
        event.preventDefault();
        setStatus(title.trim() && content.trim() ? "saved" : "invalid");
      }}
    >
      <label className="legacy-form-label">
        {labels.titleLabel}
        <input
          className="legacy-search"
          onChange={(event) => {
            setTitle(event.target.value);
            setStatus("idle");
          }}
          value={title}
        />
      </label>
      <label className="legacy-form-label">
        {labels.typeLabel}
        <select
          className="legacy-search"
          onChange={(event) => {
            setPostType(event.target.value === "share" ? "share" : "question");
            setStatus("idle");
          }}
          value={postType}
        >
          <option value="question">{labels.typeQuestion}</option>
          <option value="share">{labels.typeShare}</option>
        </select>
      </label>
      <label className="legacy-form-label">
        {labels.contentLabel}
        <textarea
          className="legacy-prompt-area"
          onChange={(event) => {
            setContent(event.target.value);
            setStatus("idle");
          }}
          value={content}
        />
      </label>
      {status === "invalid" ? (
        <p className="legacy-inline-alert" role="alert">
          {labels.validationError}
        </p>
      ) : null}
      {status === "saved" ? (
        <div className="legacy-draft-preview" role="status">
          <span>{labels.draftSaved}</span>
          <em>{labels.previewTitle}</em>
          <strong>{title}</strong>
          <p>{content}</p>
        </div>
      ) : null}
      <div className="legacy-form-actions">
        <button className="legacy-primary-button" type="submit">
          {labels.submit}
        </button>
        <button
          className="legacy-secondary-button"
          onClick={() => {
            setTitle(labels.titleValue);
            setContent(labels.contentValue);
            setPostType("question");
            setStatus("idle");
          }}
          type="button"
        >
          {labels.reset}
        </button>
        <Link className="legacy-secondary-button" href="/board">
          {labels.backBoard}
        </Link>
      </div>
    </form>
  );
}
