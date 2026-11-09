# Expert review author display

Migration029 installed by the owner on 2026-11-09. Independent read-only hosted metadata verification confirms all four preflight flags plus one exact saved-author projection match. No account or screening rows were read. Do not rerun029. Actual reviewed-name native display remains unverified.

The Expo report's Expert review section shows Reviewed by, using
`review.expert_name`. With no saved reviewer it shows Not yet reviewed. An older
server response with a reviewer ID but no name shows Name unavailable.

For a fresh environment after028, the database owner runs
`db/postgres/029_review_expert_name.sql`, followed by the read-only
`db/postgres/029_review_expert_name_preflight.sql`. All four flags should be true.
The current hosted project is already verified installed. Do not rerun029 or
earlier migrations there. Refresh the report to load the installed projection.

029 adds only the current display name of the profile identified by the saved
validation's expert_id to the existing authorized screening/report projection.
It never substitutes the current assigned expert. It preserves historical
authorship IDs, scoped visibility, parent Validated-only release, session gates,
function privileges and records. A later profile rename updates the displayed
name; this is not a frozen historical name snapshot. Missing authors remain null.

The existing Python ScreeningReadService passes the additional field through;
no API restart is required. OpenAPI declares it optional for compatibility with
responses before029. Existing legacy Flask reports already resolve expert_name
from the validation author and are unchanged. The app source remains local;
the published APK requires rebuilding before it can show this field.

Offline checks run through `node graphiscan/tools/check_api_contract.cjs` and
mobile `npm.cmd run typecheck`. They do not apply029 to the hosted project or
submit an expert review.
