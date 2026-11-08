# Frequently asked questions

## Is the course complete?

Not yet. The architecture, syllabus, module plans, rubrics, and repository
standards are published. **The foundation sequence F01-F13 is available now** as
complete lessons with executable notebooks, labs, and assessments; it delivers
M01-M03. The remaining lessons are being authored in the phases described in
[Implementation phases](../planning/implementation-phases.md). Pages and
notebooks are marked as planned until they have been executed and reviewed.

## Do I need a GPU?

No for the CPU track. You need a GPU for the core labs in M07-M08 (fine-tuning),
M12 (detector training), and the heavier M14 video experiments. Free Google
Colab and Kaggle GPU tiers are supported. Every module states its hardware
requirement.

## What does it cost?

The core course uses free and open-source tools. You need a computer with
internet access. Optional costs include cloud storage, paid APIs, or a local GPU.
No paid service is required to complete the course.

## Do I need to know calculus and linear algebra?

You need high-school algebra and comfort with basic statistics. The course
introduces vectors, derivatives, and probability where they are used. If you want
extra preparation, review vectors, matrices, derivatives, and descriptive
statistics before M02.

## How much Python do I need?

You should be able to write functions, use lists and dictionaries, read and write
files, install packages, and use the command line. If not, start with
[F01 - Python essentials for AI](../lessons/f01-python-ai/index.md). F02 covers
environments, not programming fundamentals.

## How long will it take?

The full program is about 339 guided hours. At 13 hours per week, plan for about
26 weeks. The [roadmap](roadmap.md#study-schedules) gives 13-week, 26-week,
42-week, and 16-week semester schedules. Labs often take longer the first time.

## Is there a certificate or university credit?

No. This is a public self-study resource. Completing it does not automatically
grant credit, a certificate, or a professional qualification. Enrolled students
follow their institution's rules. You can use the rubrics and portfolio as
evidence of your work.

## Can I use a Mac or Linux?

Yes. The instructions target Windows 11 and Google Colab, but almost everything
works on macOS and Linux. Windows-specific setup notes are in
[Troubleshooting](../technical/troubleshooting.md).

!!! warning "What has actually been verified"
    The recorded executions in this release are on Windows 11 CPU. macOS, Linux,
    and Google Colab are supported targets, but their notebooks, lab runs, and
    GPU paths have not been verified here, so treat platform-specific output as
    unconfirmed rather than as a tested result.

## Can I use an AMD or Intel GPU?

The supported GPU path is NVIDIA CUDA, plus free Colab/Kaggle GPUs. AMD and Intel
GPUs can work with additional setup, but the course does not guarantee support.
When in doubt, use Colab or a CPU-feasible variant of the lab.

## Do I need API keys or a paid LLM?

No. Language modules support small open models that run locally or on free GPU
tiers. Hosted APIs are optional for convenience, comparison, or agent labs. Never
commit API keys to the repository.

## Where do the datasets come from?

Each module uses small, legal-to-use datasets or synthetic data, with a dataset
card stating the source, license, and limitations. The repository never commits
raw datasets. Download scripts will be provided with the notebooks.

## What if a dataset license changes or a link breaks?

Report it through GitHub Issues with the module code. Dataset links and licenses
are reviewed during the quality checks for each implementation phase.

## Can I use ChatGPT or another AI assistant?

Yes, as a tutor, reviewer, and debugging aid, with disclosure. Do not submit
AI-generated work as your own, and verify every API, statistic, and citation.
See the integrity rules in [How to study](how-to-study.md#academic-integrity-and-ai-assistants).

## How do I get help?

Use the repository's GitHub Issues. Include the module code, expected and actual
behavior, versions, hardware, and a minimal reproduction. Do not share private
data or secrets.

## Can I contribute a module or lab?

Yes, after reading [Contributing](../technical/contributing.md) and the
[quality standards](../planning/quality-standards.md). Contributions must use
legal data, include evaluation, and pass review. The instructor decides scope and
sequencing.

## Will this help me get a job?

It can help you build credible evidence: working systems, evaluation reports,
documentation, and a capstone. No course can guarantee employment. Employers
value demonstrated ability, clear communication, and honest limitations - which
is exactly what the labs and capstone are designed to produce.

## Why are some modules marked GPU required?

Training compute is real. Fine-tuning, detector training, and video-model
training are slow or infeasible on a CPU within a reasonable study session. The
course keeps these requirements explicit instead of pretending a laptop CPU is
enough. GPU-free alternatives are provided where they preserve the learning
outcome.

## Is the course safe and ethical?

The course teaches lawful, responsible applications and explicitly excludes face
recognition, covert surveillance, non-consensual voice cloning, and other harmful
uses. You are responsible for the laws, institutional policies, and dataset
licenses that apply to your work.

## How is the site built?

The site is built with MkDocs Material from the `docs/` directory. Build and
deployment instructions are in
[Build and deploy](../technical/build-and-deploy.md). Students do not need to
build the site to use the course.
