# V41R27R15 Python runtime image qualification record

## State slice

`V41R27R15PythonRuntimeImageQualification`

The fresh no-model H100 canary used the provider `cuda-12.4` image with a
15-minute, `$0.9990` ceiling. It confirmed Python 3.10.12 at
`/usr/bin/python3`, pip, git, an H100 80GB at compute capability 9.0, and driver
580.159.03. The six frozen Python dependencies were initially absent.

The sole installation command failed with exit 128 while cloning the private
RGS repository. No credentials or substitute source were used. Dependencies
were not installed; no model, adapter, optimizer, update, assessment, or worker
was accessed. The node was stopped and the mission reported zero accrued cost.

V41R27R15 is terminal as
`V41R27R15PrivateSourceTransportFailureBeforeDependencyInstall`. A future
identity must use a locally generated, content-addressed provider context for
the authorized RGS commit and validate it before installation. Qualification
remains `NotAssessed` at 26 of 48 workers.
