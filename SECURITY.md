# Security

z0evals is public. Treat every committed study artifact, receipt, figure, and generated page as publishable.

Do not commit:

- API keys, provider tokens, cookies, pairing credentials, or `.env` files
- private prompts, personal conversations, user-identifying traces, or private filesystem snapshots
- unredacted local runtime directories such as `~/.z0int/shadow` or `~/.hermes`
- unpublished third-party data that we do not have permission to redistribute

Security-sensitive findings should not be opened as public exploit details. Contact the repository owner privately.

The import path is intentionally allowlist-only and revision-pinned. Unknown provenance or a failed artifact hash must fail closed.

Verified OSS Loop review/receipt automation never grants autonomous merge authority.
