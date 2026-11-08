"use client";

import { useState } from "react";

export default function Citation({
  id,
  title,
  author = "zer0 research",
  year,
  url,
  note,
}: {
  id: string;
  title: string;
  author?: string;
  year: number;
  url: string;
  note?: string;
}) {
  const [copied, setCopied] = useState(false);
  const bib = `@misc{${id},\n  title  = {${title}},\n  author = {${author}},\n  year   = {${year}},\n  url    = {${url}}${note ? `,\n  note   = {${note}}` : ""}\n}`;
  return (
    <div className="es-cite">
      <div className="es-cite-text">
        {author}, &ldquo;{title}&rdquo;, z0evals, {year}.
      </div>
      <div className="es-cite-box">
        <pre>{bib}</pre>
        <button
          type="button"
          onClick={() => {
            navigator.clipboard?.writeText(bib).then(() => {
              setCopied(true);
              setTimeout(() => setCopied(false), 1500);
            });
          }}
        >
          {copied ? "copied" : "copy bibtex"}
        </button>
      </div>
    </div>
  );
}
