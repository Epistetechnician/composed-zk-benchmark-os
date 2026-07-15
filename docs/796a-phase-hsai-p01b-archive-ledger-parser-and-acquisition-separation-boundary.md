# Phase 796-A HSAI P01B Archive Ledger Parser and Acquisition Separation Boundary

## Status

Complete as a documentation-first parser and acquisition-separation boundary.

State slice:
`phase-796a-hsai-p01b-archive-ledger-parser-and-acquisition-separation-boundary`.

Classification: `P01BArchiveLedgerParserBoundarySpecified`.

Execution status: `NotRun`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Verdict

Phase 796-A is the first remediation workstream under the Phase 796 stop. It
defines one future hermetic parser implementation and an independently
authorized later acquisition-only run. It does not authorize either action in
this documentation slice.

The workstream is intentionally split:

```text
796-A   documentation-first parser and acquisition-separation boundary
796-A1  additive hermetic parser implementation and synthetic tests
796-A2  independent source, test, and contract audit
796-A3  separately authorized acquisition-only candidate-ledger run
796-A4  independent candidate-ledger review and accepted-bound proposal
796-A5  local repository two-reviewer accepted-bound decision
```

`796-A` is an umbrella remediation identifier, not immediate authority to
download or inspect the pinned archive. A later run may occur only after the
parser implementation is committed cleanly and Phase 796-A2 returns a zero-gap
review.

Every sub-slice preserves:

```text
preparation_contract_sha256 = absent
phase_797_authorized = false
materialization_authorized = false
capture_authorized = false
```

## Governing Sources

The gzip grammar is governed by
[RFC 1952](https://www.rfc-editor.org/rfc/rfc1952.html). A gzip file can contain
a sequence of members; this P01B profile deliberately admits exactly one. Each
member has a fixed header, optional fields, a DEFLATE payload, and a
CRC32/ISIZE trailer. Reserved flags must be zero and every checksum must be
verified by the new parser rather than hidden behind a convenience decoder.

The TAR grammar is bounded to strict ustar and one local extended-header shape
from the [POSIX `pax` interchange format](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/pax.html),
plus the one GNU long-name extension admitted by the historical helper. The
[GNU TAR format description](https://www.gnu.org/software/tar/manual/html_node/Standard.html)
documents incompatible GNU and sparse extensions; this boundary rejects them
rather than treating them as ordinary files.

These sources define syntax. Repository policy below is deliberately stricter
than general-purpose gzip or TAR compatibility.

## Pinned Input Authority

The only production-shaped asset under this workstream is:

```text
asset_id = aeneas-main-nightly-2026-07-10-c2015b8
url = https://github.com/AeneasVerif/aeneas/releases/download/nightly-2026.07.10-c2015b8/aeneas-macos-aarch64.tar.gz
release_id = 351909376
github_asset_id = 472143319
filename = aeneas-macos-aarch64.tar.gz
tag_commit = c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d
compressed_bytes = 123234656
sha256 = fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45
release_immutable = false
```

Mutable release metadata cannot replace the pinned length and SHA-256.
Redirect targets, HTTP metadata, TLS success, filenames, and release-page state
are transport observations only.

The main archive contains the separately published Lean-build asset at:

```text
backends/lean/.lake/lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz
```

The accepted logical member must have:

```text
bytes = 50447755
sha256 = f1771437f16e5e34135719ff467b32ecda101cc215dc411741cd098732916f59
```

Phase 796-A does not need a second network download to check that embedded
member identity. Reacquiring the separate asset requires its own explicit
operation row.

## Existing Helper Separation

The historical helper remains unchanged:

```text
tools/hsai-formal-preflight/raw_archive_validator.py
sha256 = 31fa2450fe7e3ce87c13dd844ac6fde1cde0a4a81e7d351276e5dd2a4ba32692
```

It is retained for historical Phase 749 and Phase 741 correspondence. It uses
`gzip.GzipFile`, records selected TAR fields, accepts signed-checksum
compatibility, and commits only the legacy five-field structural inventory. It
does not expose complete gzip framing, complete physical TAR headers,
per-regular-file content digests, or extraction bounds.

Phase 796-A1 must add a separate helper. It may not modify, import, wrap, or
silently replace the historical helper.

## Conditionally Authorized Phase 796-A1 Surface

Only after this boundary is committed and independently reviewed, Phase 796-A1
may modify exactly:

```text
tools/hsai-formal-preflight/p01b_archive_ledger.py
tools/hsai-formal-preflight/tests/test_p01b_archive_ledger.py
docs/796a1-phase-hsai-p01b-archive-ledger-parser-implementation.md
README.md
docs/12-task-list.md
docs/90-whole-codebase-validation-report.md
AGENTS.md
```

The helper must use only the Python 3.9.6 standard library available to the
existing formal-preflight lane. It may use `hashlib`, `json`, `os`, `resource`,
`stat`, `struct`, `tempfile`, and `zlib`. It may not use `gzip.GzipFile`,
`tarfile`, an external `gzip` or `tar` executable, a shell, subprocess, network,
environment lookup, package installation, dynamic import, or external
dependency.

The implementation is hermetic. Tests construct all synthetic archives under
test-owned temporary directories. Phase 796-A1 may not read the real Aeneas
asset, create durable candidate ledgers, or perform network access.

## Future Hermetic CLI

The only future production-shaped parser argv is:

```json
["/usr/bin/python3","-B","${DETACHED_ROOT}/tools/hsai-formal-preflight/p01b_archive_ledger.py","inspect","--download-root","${DOWNLOAD_ROOT}","--archive","${DOWNLOAD_ROOT}/aeneas-macos-aarch64.tar.gz","--attempt-root","${ATTEMPT_ROOT}","--candidate-parent","${ATTEMPT_ROOT}/phase-796a"]
```

The CLI accepts no caller-selected URL, expected digest, expected length,
profile, limit, output filename, parser mode, compatibility flag, or extension
allowlist. Those values are constants in the reviewed helper. Abbreviated
options and additional positional arguments fail.

`stdin` is closed. Successful stdout is one canonical status line. Stderr is
empty. Failure emits no stdout and one bounded canonical error line on stderr.
No traceback or raw archive-controlled string may be emitted.

The future bounded-runner contract must set:

```text
timeout_seconds = 1800
cpu_seconds = 900
max_open_file_descriptors = 32
stdout_cap_bytes = 16384
stderr_cap_bytes = 16384
stdin = null
network = closed
```

Phase 796-A1 must set enforceable CPU, output-file, and descriptor limits before
opening input. The current macOS `/usr/bin/python3` and bounded runner do not
provide an accepted enforceable resident-memory limit. Phase 796-A3 therefore
remains blocked until a separately authorized process supervisor proves an
enforced `max_resident_bytes=536870912` contract. Phase 796-A1 may implement and
test the streaming parser but may not weaken or claim that missing acquisition
containment. These are parser-run bounds only. The preceding downloader remains
the exact Phase 782 ordinal-033 operation and has its own timeout and transcript
caps.

## Input Object Contract

The helper must:

1. require normalized absolute `DOWNLOAD_ROOT`, archive, `ATTEMPT_ROOT`, and
   candidate-parent paths;
2. reject NUL, dot, dot-dot, repeated-separator, and trailing-separator forms;
3. require the archive to be beneath exactly one accepted `DOWNLOAD_ROOT`, the
   candidate parent beneath exactly one accepted `ATTEMPT_ROOT`, and all input
   and output roots to be pairwise non-overlapping;
4. open and retain accepted root directory descriptors, traverse every child
   component descriptor-relatively with no-follow entry/open comparisons, and
   reject symlink or directory identity drift before opening the terminal;
5. open the archive terminal once with read-only, no-follow, and close-on-exec
   flags relative to the retained `DOWNLOAD_ROOT` descriptor;
6. require a regular non-symlink object of exactly 123,234,656 bytes;
7. record device, inode, mode, owner, link count, length, modification time,
   and change time before parsing;
8. hash and parse through duplicated descriptors for the same retained object;
9. reject any retained-root, ancestor, terminal, metadata, or SHA-256 drift;
   and
10. require the pinned archive SHA-256 before candidate publication.

No archive pathname may be reopened after descriptor acceptance. A path label
is diagnostic only and does not substitute for object identity.

## Fixed Resource Limits

Phase 796-A1 must compile these constants into the helper:

```text
READ_CHUNK_BYTES = 65536
GZIP_MEMBERS = 1
MAX_GZIP_FILENAME_BYTES = 4096
MAX_GZIP_COMMENT_BYTES = 4096
MAX_GZIP_EXTRA_BYTES = 65535
MAX_GZIP_OPTIONAL_BYTES_TOTAL = 73727
MAX_COMPRESSION_RATIO = 72
MAX_UNCOMPRESSED_TAR_BYTES = 8589934592
MAX_PHYSICAL_TAR_HEADERS = 8192
MAX_LOGICAL_MEMBERS = 4096
MAX_EXTENSION_HEADERS = 512
MAX_EXTENSION_PAYLOAD_BYTES = 65536
MAX_EXTENSION_PAYLOAD_BYTES_TOTAL = 4194304
MAX_MEMBER_BYTES = 1073741824
MAX_AGGREGATE_REGULAR_BYTES = 6442450944
MAX_TOTAL_EXTRACTION_OUTPUT_BYTES = 6442450944
MAX_EFFECTIVE_PATH_BYTES = 1024
MAX_PATH_COMPONENT_BYTES = 255
MAX_PATH_COMPONENTS = 128
MAX_TRAILING_ZERO_BYTES = 1048576
MAX_HEADER_LEDGER_BYTES = 67108864
MAX_INVENTORY_LEDGER_BYTES = 16777216
MAX_MANIFEST_BYTES = 1048576
MAX_STATUS_BYTES = 65536
MAX_TOTAL_CANDIDATE_BYTES = 85000192
```

Every counter uses checked nonnegative integer arithmetic. A bound is checked
at `N` and rejected at `N+1` before allocating, buffering, hashing, skipping,
or publishing the bounded object. The parser keeps at most one 64-KiB stream
chunk, one 512-byte TAR header, and one bounded extension payload beyond
canonical output buffers.

The compression ratio is the final uncompressed TAR byte count divided by the
exact compressed asset byte count, compared without floating point.
`MAX_TOTAL_EXTRACTION_OUTPUT_BYTES` is the sum of accepted logical regular-file
sizes. Directories contribute zero. No member is actually extracted.

## Gzip Framing Contract

The helper must parse the sole RFC 1952 member directly:

1. require `ID1=0x1f`, `ID2=0x8b`, and `CM=8`;
2. reject every reserved `FLG` bit;
3. record exact raw fixed-header bytes and decoded `FLG`, `MTIME`, `XFL`, and
   `OS`;
4. parse and bind every present `FEXTRA`, `FNAME`, and `FCOMMENT` byte;
5. verify FEXTRA subfield framing and every present `FHCRC`;
6. stream raw DEFLATE through `zlib.decompressobj(wbits=-15)`;
7. account exactly for compressed bytes consumed and output bytes emitted;
8. verify trailer `CRC32` over the complete uncompressed TAR bytes;
9. verify trailer `ISIZE` against output length modulo 2^32;
10. reject overlong optional fields before searching beyond their limits;
11. reject truncated streams, malformed DEFLATE, empty input, a second member,
    trailing zeroes, and every byte after the sole trailer; and
12. feed uncompressed output into one continuous TAR block parser without
    materializing the full TAR stream.

The gzip ledger records compressed offsets, raw fixed and optional fields,
optional-field lengths and SHA-256 values, header CRC presence/value, DEFLATE
byte range and digest, raw trailer bytes, trailer offset, trailer CRC32, trailer
ISIZE, actual 64-bit output bytes, raw member SHA-256, and uncompressed TAR
SHA-256.

## TAR Physical Grammar

The parser consumes exact 512-byte blocks. Every nonzero physical header must
have `magic="ustar\0"` and `version="00"`. Each physical-header row records:

```text
physical_header_index
uncompressed_block_index
uncompressed_byte_offset
raw_header_hex
raw_header_sha256
raw_name_hex
raw_mode_hex
raw_uid_hex
raw_gid_hex
raw_size_hex
raw_mtime_hex
raw_checksum_hex
raw_typeflag_hex
raw_linkname_hex
raw_magic_hex
raw_version_hex
raw_uname_hex
raw_gname_hex
raw_devmajor_hex
raw_devminor_hex
raw_prefix_hex
raw_padding_hex
parsed_size
parsed_checksum
checksum_variant
```

All hexadecimal text is lowercase. Numeric fields are canonical bounded ASCII
octal with NUL/space termination. Base-256, negative, overflow, unterminated,
and every other encoding are rejected. The stored checksum must equal the
POSIX unsigned-byte calculation. Signed-only checksum compatibility is
rejected; `checksum_variant` is therefore exactly `unsigned-posix-v1`.

The accepted numeric bytes are exact:

```text
mode[8]      = seven bytes in "0".."7", then NUL
uid[8]       = seven bytes in "0".."7", then NUL
gid[8]       = seven bytes in "0".."7", then NUL
size[12]     = eleven bytes in "0".."7", then NUL
mtime[12]    = eleven bytes in "0".."7", then NUL
checksum[8]  = six bytes in "0".."7", then NUL, then ASCII space
devmajor[8]  = seven bytes in "0".."7", then NUL
devminor[8]  = seven bytes in "0".."7", then NUL
```

Leading spaces, trailing spaces outside the checksum form, omitted terminators,
additional terminators, signs, and non-octal digits fail. Values are parsed in
base eight with checked `u64` arithmetic. During checksum calculation, bytes
148 through 155 are treated as eight ASCII spaces.

The accepted string-field bytes are exact:

```text
name[100], linkname[100], uname[32], gname[32], prefix[155]
```

A string field is either completely filled with permitted ASCII bytes or has
one first NUL followed only by NUL bytes. Bytes after the first NUL may not be
ignored. `name` is nonempty. `linkname` is empty for every admitted type.
`uname` and `gname` may be empty; nonempty values use printable ASCII. `prefix`
may be empty; when nonempty, the raw base path is exactly
`prefix + "/" + name`. Neither side of that join may contain a leading or
trailing separator. Header bytes 500 through 511 are exactly zero.

The helper records but assigns no extraction authority to mode, uid, gid,
mtime, uname, or gname. `devmajor` and `devminor` must decode to zero for every
admitted type. No host locale, filesystem encoding, Python TAR behavior, or
last-value-wins rule participates in field interpretation.

Exactly these physical type flags are admitted:

```text
NUL or "0"  regular file
"5"         directory
"x"         local POSIX PAX extended header
"L"         GNU long-name extension
```

Global PAX, Solaris and star extensions, GNU long links, GNU sparse, old-GNU
sparse continuations, hard links, symbolic links, devices, FIFOs, contiguous
files, sockets, whiteouts, volume headers, multi-volume records, and unknown
types are rejected. A directory must have size zero.

Every regular member is streamed for content SHA-256. Every member padding byte
must be zero. Exactly two consecutive all-zero 512-byte blocks terminate the
archive. Remaining bytes must be zero and within
`MAX_TRAILING_ZERO_BYTES`. A single zero block followed by a header, a partial
block, nonzero trailing data, or a missing terminator fails.

## Extension Semantics

A local PAX payload is parsed as exactly one record:

```text
<decimal length><space>path=<ASCII value><LF>
```

Leading signs, leading zeroes, missing separators, inconsistent lengths,
embedded NUL, non-ASCII bytes, empty keys or values, duplicate records,
additional records, unknown keys, and unconsumed bytes fail. PAX `size`, sparse,
vendor, deletion, and global semantics are rejected.

A GNU long-name payload must contain printable ASCII path bytes, end in exactly
one NUL, contain no earlier NUL, remain within the path bound, and apply to
exactly the next logical member. PAX and GNU path overrides may not stack or
conflict. An orphan extension, multiple pending extensions, mixed extension
types, or an extension followed by another extension fails.

## Logical Name and Inventory Contract

Effective path bytes must be ASCII `0x20` through `0x7e`, excluding backslash.
Names are relative POSIX paths. The parser rejects:

- empty and absolute names;
- NUL and control bytes;
- backslash;
- leading `./`;
- repeated separators;
- internal `.` or `..` components;
- more than 128 components;
- components over 255 bytes;
- effective names over 1,024 bytes;
- trailing separators on regular files;
- multiple trailing separators on directories;
- duplicate raw or effective names;
- duplicate normalized collision keys;
- file/directory collisions; and
- a regular-file collision key used as another member's ancestor.

No root marker is accepted because the pinned main profile requires zero root
markers. A directory's single trailing slash is removed only for its collision
key.

The complete logical inventory row is a canonical JSON object containing:

```text
schema
archive_index
physical_header_index
extension_header_indices
raw_name_hex
effective_raw_name
collision_key
kind
member_size
content_sha256
data_offset
data_padding_bytes
```

`schema` is `hsai-p01b-archive-logical-member-v1`. `kind` is exactly `regular`
or `directory`; directory content SHA-256 is the empty-byte SHA-256.

For historical correspondence the helper also recomputes, but does not emit as
the new ledger, the legacy compact JSON-LF rows:

```text
[archive_index,effective_raw_name,collision_key,kind,member_size]
```

Rows are sorted by their full tuple exactly as the retained Phase 749 helper
does. The required legacy inventory SHA-256 is:

```text
26c0f52d30c7fd254ec76f3ee796a769c51eda9fbd72b0f9592e4b70d665539e
```

## Required Candidate Profile

Candidate publication requires all of these exact profile values:

```text
gzip_members = 1
logical_members = 2471
root_count = 0
regular_members = 2305
directory_members = 166
top_level = [aeneas,backends,charon,charon-driver,libs,rust-toolchain]
legacy_inventory_sha256 = 26c0f52d30c7fd254ec76f3ee796a769c51eda9fbd72b0f9592e4b70d665539e
embedded_lean_bytes = 50447755
embedded_lean_sha256 = f1771437f16e5e34135719ff467b32ecda101cc215dc411741cd098732916f59
```

Observed physical-header count, extension-header count, uncompressed TAR bytes,
aggregate regular bytes, largest member bytes, and trailing zero bytes must fit
the fixed limits and are emitted as candidate measurements. They are not
accepted extraction bounds merely because one run observes them.

## Canonical Candidate Artifacts

The successful candidate root contains exactly:

```text
archive-source-manifest-v1.json
gzip-tar-header-ledger-v1.jsonl
ordered-logical-member-inventory-v1.jsonl
archive-ledger-capture-status-v1.json
```

Every JSON object is encoded with UTF-8, `ensure_ascii=true`, lexicographically
sorted object keys, compact separators, no insignificant whitespace, no BOM,
and exactly one terminal LF. Integers are unsigned decimal JSON integers except
the two explicitly signed descriptor timestamp-second fields; floating point,
exponent forms, negative zero, and `null` are forbidden.
JSONL order is semantic and may not be resorted after generation.

The archive-ledger contract digest is:

```text
SHA256(
  ASCII("hsai:p01b-archive-ledger-contract:v1\0") ||
  canonical_json(contract_object)
)
```

`canonical_json` is the exact one-line encoding above without its terminal LF.
`contract_object` has exactly these keys and values. Canonical encoding sorts
the keys lexicographically:

```text
boundary_document_sha256 = lowercase SHA-256 of this committed Markdown file
candidate_artifact_schemas = sorted array containing exactly:
  hsai-p01b-archive-ledger-capture-status-v1
  hsai-p01b-archive-source-manifest-v1
  hsai-p01b-gzip-tar-header-ledger-v1
  hsai-p01b-ordered-logical-member-inventory-v1
failure_taxonomy_schema = hsai-p01b-archive-ledger-failure-v1
grammar_profile = hsai-p01b-single-gzip-strict-ustar-v1
limits = object formed from every NAME=integer line in Fixed Resource Limits,
         with exactly those names and values and lexicographically sorted keys
schema = hsai-p01b-archive-ledger-contract-v1
```

No implementation digest, host fact, run receipt, or candidate measurement is
part of this contract digest. Those values bind to it later. Phase 796-A1 must
publish the committed boundary-document SHA-256, canonical contract-object
bytes, and resulting contract digest as golden vectors.

This boundary file is immutable in the Phase 796-A1 surface. Any correction to
its bytes requires a separately authorized contract-correction phase, a new
grammar-profile version, and new golden vectors; implementation may not rewrite
the document it claims to implement.

The source manifest binds:

- the pinned asset authority;
- all fixed limits and the contract digest;
- parser source SHA-256;
- observed Python and zlib versions, explicitly marked non-authoritative;
- archive descriptor identity and SHA-256;
- all observed profile measurements;
- both ledger byte lengths and SHA-256 values; and
- `candidate_only=true`, `accepted=false`, and all four false authority fields.

The header ledger contains ordered `gzip_member`, `tar_header`,
`tar_terminator`, and `tar_trailing_padding` rows. Extension-header rows include
the exact payload as lowercase hex and its SHA-256. The logical ledger contains
only ordered logical-member rows.

The status object is written last. It binds the manifest and both ledgers,
reports `decision=candidate_generated`, and carries no stronger authority. No
artifact digest depends on a later artifact, so the digest graph is acyclic.

The parser cannot authenticate its own executable, argv, environment, or
supervisor. The later Phase 796-A3 run receipt must externally bind accepted
Python executable facts, parser source and contract digests, exact argv,
replacement environment, process limits, archive descriptor identity, and all
four candidate artifact digests.

## Exact Artifact Schemas

No field in the four artifacts is optional. Unknown or duplicate keys fail.
`u64` means a JSON integer from zero through 18,446,744,073,709,551,615.
`hex` means lowercase even-length hexadecimal, and `sha256` means exactly 64
lowercase hexadecimal characters. An absent gzip optional field is represented
by `present=false`, `bytes=0`, `hex=""`, and the SHA-256 of empty bytes. An
absent numeric value is represented by its companion `present=false` and
integer zero. `null` is never used.

### Source manifest object

`archive-source-manifest-v1.json` contains one object with exactly:

```text
schema: "hsai-p01b-archive-source-manifest-v1"
asset_id: ASCII string
url: ASCII string
release_id: u64
github_asset_id: u64
filename: ASCII string
tag_commit: exactly 40 lowercase hexadecimal characters
expected_compressed_bytes: u64
expected_archive_sha256: sha256
release_immutable: bool
contract_digest: sha256
parser_source_sha256: sha256
python_version: ASCII string
zlib_version: ASCII string
archive_device: u64
archive_inode: u64
archive_mode: u64
archive_owner_uid: u64
archive_link_count: u64
archive_byte_length: u64
archive_modified_seconds: signed JSON integer
archive_modified_nanoseconds: u64 in 0..999999999
archive_changed_seconds: signed JSON integer
archive_changed_nanoseconds: u64 in 0..999999999
archive_sha256: sha256
gzip_members: u64
physical_tar_headers: u64
logical_members: u64
root_count: u64
regular_members: u64
directory_members: u64
extension_headers: u64
uncompressed_tar_bytes: u64
aggregate_regular_bytes: u64
largest_member_bytes: u64
trailing_zero_bytes: u64
top_level: sorted unique array of ASCII strings
legacy_inventory_sha256: sha256
embedded_lean_bytes: u64
embedded_lean_sha256: sha256
header_ledger_bytes: u64
header_ledger_sha256: sha256
inventory_ledger_bytes: u64
inventory_ledger_sha256: sha256
candidate_only: true
accepted: false
phase_797_authorized: false
materialization_authorized: false
capture_authorized: false
accepted_evidence_authorized: false
```

### Header-ledger row order

`gzip-tar-header-ledger-v1.jsonl` emits rows in exactly this order:

```text
one ledger_header row
all physical tar_header rows in increasing physical_header_index
one tar_terminator row
one tar_trailing_padding row, including when its byte count is zero
one gzip_member row
```

Every row has a contiguous `row_index` beginning at zero. The gzip summary is
last because its trailer and complete uncompressed digest are unavailable until
the TAR stream has ended.

The header-ledger `ledger_header` row has exactly:

```text
schema: "hsai-p01b-gzip-tar-header-ledger-v1"
row_kind: "ledger_header"
row_index: 0
contract_digest: sha256
```

Each `tar_header` row has exactly:

```text
schema: "hsai-p01b-tar-header-v1"
row_kind: "tar_header"
row_index: u64
physical_header_index: u64
uncompressed_block_index: u64
uncompressed_byte_offset: u64
raw_header_hex: exactly 1024 lowercase hexadecimal characters
raw_header_sha256: sha256
raw_name_hex: exactly 200 lowercase hexadecimal characters
raw_mode_hex: exactly 16 lowercase hexadecimal characters
raw_uid_hex: exactly 16 lowercase hexadecimal characters
raw_gid_hex: exactly 16 lowercase hexadecimal characters
raw_size_hex: exactly 24 lowercase hexadecimal characters
raw_mtime_hex: exactly 24 lowercase hexadecimal characters
raw_checksum_hex: exactly 16 lowercase hexadecimal characters
raw_typeflag_hex: exactly 2 lowercase hexadecimal characters
raw_linkname_hex: exactly 200 lowercase hexadecimal characters
raw_magic_hex: exactly 12 lowercase hexadecimal characters
raw_version_hex: exactly 4 lowercase hexadecimal characters
raw_uname_hex: exactly 64 lowercase hexadecimal characters
raw_gname_hex: exactly 64 lowercase hexadecimal characters
raw_devmajor_hex: exactly 16 lowercase hexadecimal characters
raw_devminor_hex: exactly 16 lowercase hexadecimal characters
raw_prefix_hex: exactly 310 lowercase hexadecimal characters
raw_padding_hex: exactly 24 lowercase hexadecimal characters
base_name: ASCII string
prefix: ASCII string
parsed_mode: u64
parsed_uid: u64
parsed_gid: u64
parsed_size: u64
parsed_mtime: u64
parsed_checksum: u64
parsed_devmajor: u64
parsed_devminor: u64
checksum_variant: "unsigned-posix-v1"
member_type: one of "regular", "directory", "pax_path", "gnu_long_name"
extension_payload_present: bool
extension_payload_bytes: u64
extension_payload_hex: hex
extension_payload_sha256: sha256
applies_to_archive_index_present: bool
applies_to_archive_index: u64
data_offset: u64
data_bytes: u64
data_padding_bytes: u64
data_padding_sha256: sha256
```

For non-extension rows, extension payload fields use the absent representation.
For extension rows, `applies_to_archive_index_present=true`; the index names the
immediately following logical member. For non-extension rows it is false and
the index is zero. `data_bytes` equals the raw header size field for regular and
extension rows and zero for directories.

The `tar_terminator` row has exactly:

```text
schema: "hsai-p01b-tar-terminator-v1"
row_kind: "tar_terminator"
row_index: u64
first_zero_block_index: u64
first_zero_byte_offset: u64
first_zero_sha256: sha256 of 512 zero bytes
second_zero_block_index: u64
second_zero_byte_offset: u64
second_zero_sha256: sha256 of 512 zero bytes
```

The `tar_trailing_padding` row has exactly:

```text
schema: "hsai-p01b-tar-trailing-padding-v1"
row_kind: "tar_trailing_padding"
row_index: u64
uncompressed_byte_offset: u64
padding_bytes: u64
padding_sha256: sha256
```

The `gzip_member` row has exactly:

```text
schema: "hsai-p01b-gzip-member-v1"
row_kind: "gzip_member"
row_index: u64
member_index: 0
compressed_start: 0
compressed_end: u64
fixed_header_hex: exactly 20 lowercase hexadecimal characters
id1: 31
id2: 139
cm: 8
flg: u64 in 0..31
mtime: u64
xfl: u64 in 0..255
os: u64 in 0..255
fextra_present: bool
fextra_xlen_hex: exactly 4 lowercase hexadecimal characters when present,
                  empty string when absent
fextra_bytes: u64
fextra_hex: hex
fextra_sha256: sha256
fname_present: bool
fname_bytes: u64 excluding terminal NUL
fname_hex: hex excluding terminal NUL
fname_sha256: sha256 over bytes excluding terminal NUL
fcomment_present: bool
fcomment_bytes: u64 excluding terminal NUL
fcomment_hex: hex excluding terminal NUL
fcomment_sha256: sha256 over bytes excluding terminal NUL
fhcrc_present: bool
fhcrc_hex: exactly 4 lowercase hexadecimal characters when present,
            empty string when absent
fhcrc16: u64 in 0..65535, zero when absent
deflate_offset: u64
deflate_bytes: u64
deflate_sha256: sha256
trailer_offset: u64
trailer_hex: exactly 16 lowercase hexadecimal characters
trailer_crc32: u64 in 0..4294967295
trailer_isize: u64 in 0..4294967295
uncompressed_bytes: u64
raw_member_sha256: sha256
uncompressed_tar_sha256: sha256
```

### Logical-member row

Every `ordered-logical-member-inventory-v1.jsonl` row has exactly:

```text
schema: "hsai-p01b-archive-logical-member-v1"
row_kind: "logical_member"
row_index: contiguous u64 beginning at one
archive_index: contiguous u64 beginning at zero
physical_header_index: u64
extension_header_indices: array containing zero or one u64
raw_name_hex: exactly 200 lowercase hexadecimal characters from the physical
              header name field
effective_raw_name: ASCII string
collision_key: ASCII string
kind: one of "regular", "directory"
member_size: u64
content_sha256: sha256
data_offset: u64
data_padding_bytes: u64
```

Before those member rows, the inventory emits exactly one self-identifying row:

```text
schema: "hsai-p01b-ordered-logical-member-inventory-v1"
row_kind: "ledger_header"
row_index: 0
contract_digest: sha256
```

### Status object

`archive-ledger-capture-status-v1.json` contains exactly:

```text
schema: "hsai-p01b-archive-ledger-capture-status-v1"
decision: "candidate_generated"
declared_files: sorted array of the four final filenames
manifest_bytes: u64
manifest_sha256: sha256
header_ledger_bytes: u64
header_ledger_sha256: sha256
inventory_ledger_bytes: u64
inventory_ledger_sha256: sha256
candidate_only: true
accepted: false
phase_797_authorized: false
materialization_authorized: false
capture_authorized: false
accepted_evidence_authorized: false
```

## Output Transaction

The helper operates beneath an accepted existing private mode-0700
`${ATTEMPT_ROOT}/phase-796a` parent using descriptor-relative no-follow
operations. It atomically creates an absent mode-0700
`archive-ledger-candidate` directory and creates each mode-0600 regular file
with `O_EXCL`. The two ledgers are streamed first, reread with duplicate-key
rejection, and verified against their counts and digests. The manifest is
written next and the status record last.

The helper fsyncs each of the first three files, writes the complete status bytes
to `.archive-ledger-capture-status-v1.pending` with `O_EXCL`, fsyncs that file,
and fsyncs the candidate directory. It then atomically hard-links the fsynced
pending inode to `archive-ledger-capture-status-v1.json` with no replacement,
fsyncs the candidate directory, removes the pending name, fsyncs the candidate
directory again, and fsyncs the parent. If same-filesystem atomic hard-link
creation or directory fsync is unavailable, publication fails.

A candidate is published only when the final status link exists and a reader
revalidates its digests, declared-file set, manifest, and both ledgers. The
directory and pending status name are pending state, never publication. A crash
before the final link exposes no commit marker; a crash after the link leaves a
fully fsynced commit inode and complete previously fsynced artifacts.

Symlink ancestors, pre-existing candidate paths, undeclared files, short
writes, limit overflow, durability errors, stale pending state, and cleanup
errors fail. An ordinary handled failure removes only attempt-created pending
content. A crash may leave a stale incomplete directory; it is never accepted
as a candidate and requires an explicit later quarantine decision. No overwrite
or automatic stale-state reuse mode exists.

## Closed Failure Taxonomy

Phase 796-A1 must expose these stable classes:

```text
InvalidCli
InvalidInputPath
InvalidOutputPath
InputOverlap
InputOpen
InputNotRegular
InputIdentityDrift
InputLengthMismatch
InputDigestMismatch
ResourceLimitUnavailable
GzipMagic
GzipMethod
GzipReservedFlags
GzipOptionalFieldLimit
GzipExtraField
GzipHeaderCrc
GzipDeflate
GzipTrailerCrc
GzipTrailerSize
GzipMemberCount
GzipTrailingData
CompressionRatioLimit
UncompressedTarLimit
TarPartialBlock
TarMagic
TarVersion
TarChecksum
TarNumericEncoding
TarHeaderLimit
TarUnsupportedType
TarExtensionLimit
TarExtensionPayloadLimit
TarPaxGrammar
TarPaxKeyword
TarExtensionConflict
TarExtensionOrphan
TarPathEncoding
TarPathInvalid
TarDuplicateRawName
TarDuplicateEffectiveName
TarDuplicateCollisionKey
TarFileDirectoryCollision
TarRegularAncestor
TarMemberLimit
TarMemberSizeLimit
TarAggregateLimit
TarPaddingNonzero
TarTerminator
TarTrailingLimit
CandidateByteLimit
ProfileMismatch
EmbeddedLeanMismatch
OutputCollision
OutputWrite
OutputDurability
OutputPublication
```

Diagnostics are bounded and contain no raw archive-controlled path or PAX
value. Consumers match classes, not localized OS text or errno.

## Required Hermetic Tests

Phase 796-A1 must test every fixed limit at exactly `N` and `N+1` and cover:

- one deterministic safe gzip member and rejection of a second member;
- every gzip optional field and valid header CRC;
- invalid magic, method, reserved flags, extra-field framing, optional-field
  bounds, header CRC, DEFLATE, trailer CRC, trailer ISIZE, truncation, trailing
  zeroes, trailing garbage, and decompression ratio;
- valid regular, directory, ustar prefix, PAX path, and GNU long-name members;
- exact ustar magic/version and POSIX unsigned checksum;
- signed-only checksum, malformed and base-256 numeric fields;
- every rejected TAR type, extension, sparse, and multi-volume family;
- valid and malformed PAX record lengths, additional/duplicate/unknown keys,
  global PAX, size override, conflicting/orphan extensions, non-ASCII values,
  and malformed GNU long names;
- every path alias, control, backslash, duplicate, component, ancestor,
  file/directory collision, and path-length rule;
- exact and over-limit header, member, extension, extension-byte, per-member,
  aggregate regular-byte, candidate-byte, and trailing-zero cases;
- nonzero padding, one-zero terminator, missing terminator, partial block,
  member after a zero block, and nonzero trailing bytes;
- regular-file content digest and embedded Lean identity binding;
- legacy inventory digest order sensitivity;
- input symlink, ancestor symlink and directory replacement at every traversal
  checkpoint, nonregular input, root/terminal metadata drift, content drift,
  and root overlap;
- output collision, short write, ENOSPC, partial-write cleanup, durability
  failure, publication conflict, and crash injection before and after every
  file, fsync, manifest, and status step;
- declared-file-only success and deterministic replay bytes;
- canonical JSON/JSONL golden vectors, exact field-set/type checks for every row
  variant, absent gzip-option representations, contract-digest vectors, and
  duplicate/unknown-field rejection by a separate test parser; and
- source scans proving no `gzip`, `tarfile`, subprocess, shell, network,
  environment, package, extraction, or external dependency surface.

Tests use deterministic mutation checkpoints, injected readers/writers, and
synthetic streams. Sleeps, probabilistic races, real network, and the real
Aeneas asset are forbidden. General-purpose parsers may be differential test
oracles only; they are never acceptance authorities.

## Phase 796-A2 Audit Gate

Before acquisition can be considered, two independent reviews must confirm:

- implementation touches only the authorized files;
- every fixed constant and grammar rule is source-enforced;
- every failure class has a deterministic test;
- all required boundary and adversarial tests pass;
- output bytes match golden canonical vectors;
- input and output descriptor handling is fail-closed;
- A1 CPU, output-file, descriptor, and parser-internal limits are enforceable
  on the selected macOS host;
- no parser convenience API hides gzip or TAR framing;
- no extraction or network path exists;
- helper source and test SHA-256 values are published; and
- the worktree is clean at the reviewed commit.

A review finding produces another stop. Review success authorizes only a future
request for Phase 796-A3; it does not itself authorize acquisition.
Phase 796-A3 still requires the separate 512-MiB resident-memory supervisor
prerequisite and stops if that control is absent.

## Future Phase 796-A3 Acquisition Boundary

A later documentation decision must authorize one acquisition-only run. That
decision must bind the reviewed parser commit and source digest, contract
digest, accepted host executable facts, exact attempt root, exact Phase 782
ordinal-033 downloader argv, closed replacement environment, bounded
transcripts, one network-open download step, irreversible network closure
before parser launch, and cleanup.

The run order must be:

```text
create private attempt roots
recollect accepted curl and Python executable facts
run exact ordinal-033 downloader with network open
close network irreversibly for descendants
verify archive length and SHA-256
run the reviewed parser with network closed
publish one candidate root transactionally
retain bounded transcripts and candidate artifacts for review
delete downloaded archive bytes after the review-retention decision
```

The acquisition run may not edit the parser, use a shell, extract a member,
compile code, build Charon, materialize P01B targets, execute packaged content,
capture native transcripts, or mutate an accepted Evidence Ledger.

## Phase 796-A4 Review and Phase 796-A5 Acceptance

Candidate artifacts remain unaccepted until two independent reviewers verify
the source manifest, raw framing ledger, logical inventory, profile, limits,
canonical bytes, parser/run receipts, and archive digest. Review must either
publish an explicit accepted-bound proposal or reject the candidate without
partial acceptance.

The proposal cannot accept itself. Phase 796-A5 is a separately authorized
local repository decision after two independent reviewers return `accept` over
the same candidate and proposal digests. Its canonical
`hsai-p01b-archive-ledger-acceptance-v1` object must bind the contract digest,
parser source digest, Phase 796-A2 audit digest, Phase 796-A3 run-receipt digest,
all four candidate artifact digests, the Phase 796-A4 proposal digest, every
accepted extraction-limit name/value, two ordered reviewer IDs and review-record
digests, `authority_class=local_repository_review`, `decision=accepted`,
`evidence_ceiling=Level1LocalReplayOrLower`, and the complete Phase 796 nonclaim
set. The reviewers may not be the parser implementer or acquisition operator.

The acceptance object uses the same canonical JSON rules. It becomes effective
only in the clean repository commit that contains the object, both review
records, and the reviewed candidate artifacts. External consumers must pin that
commit. Git content addressing does not provide trusted time or host
anti-rollback; those remain blocker `P796-04` for a live attempt. Missing,
disagreeing, or stale reviews stop Phase 796-A without acceptance. Only a valid
retained local acceptance decision closes `P796-02`; an accepted-bound proposal
does not.

Even a valid Phase 796-A5 decision closes only blocker `P796-02`. It does not
close the Phase 796 stop, because `P796-01`, `P796-03`, `P796-04`, and
`P796-05` remain. It also does not close Phase 780 lane `L07`; that lane is the
later 102-row archive-inventory contract scheduled separately by Phase 795.

Phase 797 remains blocked until all Phase 796-A through Phase 796-F workstreams
close and the Phase 796-F independent audit publishes
`preparation_contract_sha256` from reviewed bytes.

## Mutation and Execution Record

Phase 796-A changes Markdown only. It does not implement or run the parser,
read an archive, use network, modify the historical validator, create a
candidate root, acquire source, extract a member, compile code, build a target,
materialize P01B, mutate a journal, create a plan, capture a transcript, close a
Phase 780 lane, publish a source-ledger digest, or execute a backend.

The unrelated pre-existing mutation under
`crates/hsai-agent-admission/src/lib.rs` is outside this state slice and remains
unstaged and unchanged.

## Claim Boundary

Phase 796-A is a parser and acquisition-separation design boundary. It is not a
parser implementation, parser run, archive acquisition, archive safety result,
accepted inventory, accepted extraction bound, verified build, same-object
launch proof, provisioned transaction authority, P01B materialization, target,
handoff, fixture corpus, Phase 780 lane closure, source-ledger digest, plan v2,
executor, retention result, dry preflight, live-attempt authorization, backend
execution, Lean/SMT/Z3/COBALT run, proof artifact, checker transcript, accepted
evidence, Level2+ evidence, score axis, semantic correctness, production
readiness, SOTA, breakthrough, full security, external audit, or action
authority.
