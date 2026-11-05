# Administrator-issued account delivery

Implemented locally on 2026-11-03. Sender configuration, deployment and actual
inbox delivery are not established by source changes or mocked tests.

Role-policy correction2026-11-03: apply022_mobile_password_onboarding.sql after021
before deploying this role-aware account UI. Newly issued or confirmed-reset
teacher/expert/parent accounts require first-password change. Admin/researcher
passwords are permanent from issuance/reset; normal Settings changes remain.
Existing forced flags and unresolved operations are not silently cleared.
The API retains its write-only temporary_password field name for compatibility.
Direct handover displays the confirmed receipt's flag, and email wording follows
the role. Server GRAPHISCAN_ACCOUNT_ADMIN_ACCESS_URL selects the admin portal link
(default https://admin.graphiscan.site/login); mobile mail uses
GRAPHISCAN_ACCOUNT_ACCESS_URL. Both URLs must be clean public HTTPS links.

## Creation choices

- **Give details directly:** the admin form generates
  `gs-<12 hex characters>@accounts.graphiscan.invalid`. This is a login ID, not a
  mailbox. After confirmed creation, a temporary panel shows the ID and masked
  password, with explicit Show/Hide and Done controls. Opening another creator,
  changing profile or leaving the page clears it. No browser storage or automatic
  clipboard copy is used.
- **Email login details:** enter the user's existing Gmail or other inbox. After
  confirmed Auth/profile creation, one HTTPS Brevo request sends the role-appropriate
  GraphiScan password and configured access link. Mailbox passwords are never
  requested. The link contains no credentials or authentication bypass.

Both retain role-appropriate first-password change, explicit privacy acceptance and
existing server role/school/ownership checks. Issuance creates no permission grant,
student relationship or agreement acceptance automatically.

## Setup without buying a domain

1. Register/sign in to Brevo with a team-controlled inbox. Complete account
   activation and sender verification. A free Gmail sender may be rewritten to a
   compliant provider address; verify the actual sender appearance and delivery.
2. Generate a Brevo **API key**, not an SMTP password. Enter it privately in the
   Render API environment as `GRAPHISCAN_ACCOUNT_MAIL_API_KEY`. Never put it in
   chat, Git, `VITE_*`, `EXPO_PUBLIC_*` or frontend hosting configuration.
3. Set server `GRAPHISCAN_ACCOUNT_MAIL_FROM` to the verified sender and
   `GRAPHISCAN_ACCOUNT_ACCESS_URL` to the public HTTPS installation/access page.
   The Vercel `/download/` page is suitable once its APK is actually available;
   this integration does not publish an APK. HTTP, query/fragment and credential-
   bearing URLs are refused. Missing/invalid settings disable email only.
4. Deploy reviewed API/admin source. Create one controlled test account for an
   authorized test inbox, then check provider receipt, arrival/spam, sender, access
   link, Android installation and first-password/privacy gates.

This uses `https://api.brevo.com/v3/smtp/email` over HTTPS, not SMTP networking.
Render Free blocks common SMTP ports. There is no background credential queue,
automatic resend or marketing subscription.

Official references checked 2026-11-03:

- [Render Free limitations](https://render.com/docs/free)
- [Brevo send API](https://developers.brevo.com/reference/send-transac-email)
- [Brevo free-address sender handling](https://help.brevo.com/hc/en-us/articles/14925263522578-Comply-with-Gmail-Yahoo-and-Microsoft-s-requirements-for-email-senders)

## API and recovery

`POST /api/v1/accounts` accepts optional `delivery_method: manual | email`.
Omission preserves manual issuance. Email mode rejects reserved test/login
domains. The profile reservation payload and migration018 are unchanged: **no new
database migration**. Production hosted routes use this service; older MySQL
issuance paths remain separate and are not mounted by the hosted factory.

201 returns account `data` plus response-only `credential_delivery` metadata:

| Status | Meaning |
| --- | --- |
| `manual` | Fresh account created without sending email. Give details directly. |
| `accepted` | Provider returned201 and a message ID; inbox arrival is unconfirmed. |
| `failed` | Provider definitively rejected the request (4xx except408). Account exists; direct handover remains available. |
| `unknown` | Timeout, redirect, server error or malformed receipt. Account exists; check the provider before another message, or hand over the same details. |
| `not_repeated` | Completed issuance replay. No Auth/mail replay; the supplied password is not verified and no handover panel is shown. |

Email configuration failure returns503 `ACCOUNT_EMAIL_UNAVAILABLE` before
issuance. The form stays editable for direct handover. Uncertain profile creation
retains the existing reconciliation gate and never sends email. Mail failure after
confirmed completion cannot undo creation or turn it into pending Auth issuance.

Credentials, requested delivery mode and provider bodies are not persisted in the
issuance reservation/audit or logged by this integration. The mail provider does
receive the temporary password as part of the requested message. Delivery status
is not durable inbox history. On response loss inspect the user list/provider;
never recreate the account or resend a replay body's password. If the original
password is lost, use authorized reset and direct handover. Email resend/reset
delivery is outside this slice.

## Verification

41 focused mocked Python tests, admin production build,614 contract checks and507
isolated SQL checks passed. No real mail or hosted writes were performed. Browser
checks and remaining limits are recorded in CHANGELOG.md. The earlier Python
missing-interpreter error was a sandbox access issue; approved outside-sandbox
execution uses the installed Python3.11.9 successfully.
