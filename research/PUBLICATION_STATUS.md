# DMDE publication and project links — 2 October 2026

These addresses serve different purposes:

| Address | Purpose |
|---|---|
| [Maldonado Research on GitHub](https://github.com/maldonado-research) | Account and project repository index |
| [DMDE research repository](https://github.com/maldonado-research/dmde-research) | DMDE source, reproducible calculations, dated checkpoints and current claim ledger |
| [Research homepage](https://maldonado-research.github.io/) | Readable overview of the public research projects |
| [DMDE project page](https://maldonado-research.github.io/projects/dmde/) | DMDE explanation, findings, limitations and source links |
| [HDBLAST site](https://maldonado-research.github.io/HDblast/) | Separate HDBLAST project; not the DMDE publication location |
| [DMDE Zenodo version](https://zenodo.org/records/22399940) | Preserved v0.9.20 methods/software archive |
| [DMDE all-version DOI](https://doi.org/10.5281/zenodo.18135951) | Existing DOI family for DMDE archival versions |

## Verified archive and current research

Read-only checks using the existing authorized connection confirm that
v0.9.20 is still the latest published DMDE record, with version DOI
`10.5281/zenodo.22399940` and concept DOI `10.5281/zenodo.18135951`.
The record is submitted, has nonempty metadata, and authenticated ownership
reads succeed. All five published filenames, sizes and checksums match the
original local release files. The family query returned no unsubmitted new
version. [The public verification receipt](PUBLICATION_STATUS_2026-10-02.json)
contains selected record facts and file comparisons, without credentials or
private account/draft payloads.

The [2 October source-adapter preflight](rounds/2026-10-02-source-adapter-preflight/README.md)
is a separately reviewed GitHub research checkpoint. Twelve local adapter
checks pass, while source-grid adequacy, the source-operator witness and
consistent full QED thermodynamics remain unresolved. No physical transport
history, injected BBN abundance or observational prediction is supplied.
The original Zenodo files and citation version remain frozen; later GitHub
diagnostics do not become part of that archive merely by linking them.

## Current publication workflow: automatic archiving off

The earlier signed-in browser repair synced repository access, removed a
stale entry pointing to the private archive, and temporarily enabled seven
research repositories. That state has been superseded. The authorized browser
task now reports automatic GitHub-to-Zenodo archiving **OFF** for all eight
public repositories: the seven research repositories and the shared website.
It confirmed the switches remained off after reload and their Zenodo GitHub
release histories were empty. Existing repositories, credentials, published
records and valid drafts were preserved. These switch/history observations
come from that browser handoff; the API reads here verify DMDE authentication,
record state and file identity separately.

Keep automatic archiving off. Future approved publications use the existing
authorized Zenodo connection and DMDE concept DOI `10.5281/zenodo.18135951`.
Do not create a test GitHub release, re-enable automatic archiving, or create
a second standalone record for the same work. Intended versions within one
family and genuinely separate scientific supplements are distinct from
duplicate publications. Do not delete records or drafts based on similar
titles. [The current publication handoff](PUBLICATION_HANDOFF.md) records the
latest published version and linked edit.

## Existing-record link repair and browser fallback

The existing archive has no related links to the public DMDE repository or
project page. A separately reviewed metadata-only candidate adds these two
links while preserving every original metadata field, version, DOI and file:

| Related identifier | Zenodo relationship |
|---|---|
| `https://github.com/maldonado-research/dmde-research` | `isSupplementedBy` |
| `https://maldonado-research.github.io/projects/dmde/` | `isDocumentedBy` |

The API accepted opening the existing record's metadata edit (HTTP 201),
then returned HTTP 500 when saving the complete reviewed JSON. The failure
is distinct from authentication: authorized reads and the edit action
succeeded. A fresh check confirmed all 15 original metadata fields and five
files remain intact; the public record is still published. The current edit
is populated but the two links are not saved. No publish action, new version,
GitHub release or file upload was performed. The verification receipt preserves
redacted request diagnostics. The cause of the generic server error remains
unresolved; partial replacement metadata is not a demonstrated repair.

To finish in the signed-in browser, open
[the existing v0.9.20 record](https://zenodo.org/records/22399940), choose
**Edit**, and continue its current edit. Add only the two related identifiers
above; retain the title, creator, description, license, version, date and all
five original files. Publish this existing metadata edit only after the
fields are populated and correct. Check that the public page shows both links
and retains DOI `10.5281/zenodo.22399940`. Do not select **New version** or
create another upload to resolve this administrative link update.

The [official API source](https://github.com/zenodo/developers.zenodo.org/blob/9c277efbbff8022ff4746ba471b00c8b5ed7f369/source/includes/resources/deposit/_representation.md)
documents these related-identifier fields; Zenodo's
[editing guidance](https://help.zenodo.org/docs/deposit/manage-records/)
distinguishes metadata edits from a new DOI version.

## Next archival publication

Update reviewed research records and readable website summaries as work
progresses. A new Zenodo version needs an explicitly prepared, reviewed
scientific package and accurate scope/version metadata. Numerical maintenance
and isolated component corrections alone do not warrant a new physics release.

Before uploading, inspect the latest published record, linked draft and
returned `newversion` action. Reuse a compatible existing unpublished version
draft; otherwise create the reviewed version through the latest published
version's returned action. Verify the draft belongs to concept family
`18135951` before writing. The current edit of record `22399940` is an existing
version's metadata repair, not an unsubmitted scientific version. Preserve
it and use its existing edit route for that repair. Compare the approved
local filenames, byte sizes and checksums with uploaded files;
read saved metadata back and require it to be nonempty and correct. Use
JSON for metadata and the documented binary-upload route for files. Publish
only a complete reviewed package. A reserved draft DOI or HTTP 200 alone
does not establish publication. Preserve failed redacted diagnostics and
use the existing draft's browser upload route if API transport fails.

Raw private archive files, personal documents, private scoring and tokens
remain excluded. The six-hour GitHub numerical workflow does not publish
Zenodo versions or launch an AI researcher.
