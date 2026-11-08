# Third-party licensing inventory

**Status: COMPLETE WITH UNRESOLVED UPSTREAM TERMS.** This inventory records
third-party datasets, model weights, optional dependencies, media, and external
code references. It is not legal advice and does not relicense any third-party
material.

The release tree is the set of tracked and untracked non-ignored files returned
by `git ls-files --cached --others --exclude-standard`. Generated data,
downloads, caches, and outputs are not part of that tree. A local cache or an
ignored output is **not** a redistribution.

## 1. Summary

| Question | Finding |
| --- | --- |
| Are any third-party datasets bundled? | **No.** Datasets are downloaded or supplied by the student. |
| Are any pretrained weights bundled? | **No.** Weight files are downloaded at runtime or created locally. |
| Are any third-party images, audio, or video bundled? | **No.** The tracked media files are original diagrams or generated outputs. |
| Is the SSDLite code licensed? | **Yes.** Torchvision code is BSD-3-Clause. |
| Are the SSDLite COCO weights licensed? | **Unresolved.** Torchvision states no separate weight licence and warns that weights may inherit dataset-derived terms. |
| Do fine-tuned checkpoints inherit upstream terms? | **Possibly.** Each checkpoint requires separate review; the repository licence does not resolve it. |
| Were external code examples copied? | **No copied-source notice found**, but no code-similarity audit was performed. |

## 2. External datasets

All rows are **not bundled**. "Recorded terms" means the terms stated in the
repository or by the upstream project; they were not independently re-verified
in this audit unless marked otherwise.

| Dataset / family | Source | Version or selection | Recorded terms | Redistribution | Status |
| --- | --- | --- | --- | --- | --- |
| COCO 2017 | <https://cocodataset.org/> | 2017 train/val | Annotations and site are CC BY 4.0; images remain subject to Flickr and per-image terms | Do not redistribute images without checking each image | **Unresolved image-level terms** |
| CIFAR-10 | <https://www.cs.toronto.edu/~kriz/cifar.html> | 10-class release selected by the student | Upstream dataset terms; not independently verified here | Not bundled; check the upstream page | **Unresolved upstream** |
| Fashion-MNIST | <https://github.com/zalandoresearch/fashion-mnist> | Student-selected release | Course docs describe the repository as MIT; not independently re-verified here | Not bundled; retain upstream notice if redistributed | **Pending verification** |
| DeepFashion / Fashionpedia | <http://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html> | Student-selected subset | Course docs describe DeepFashion as commonly research-only; each dataset has its own terms | No redistribution without permission | **Unresolved upstream** |
| TinyShakespeare | <https://github.com/karpathy/char-rnn> | Planned only; not used by the core path | Upstream terms not verified | Not bundled | **Unresolved upstream** |
| California Housing | scikit-learn dataset fetcher | Planned only; the core path uses synthetic tables | Upstream terms not verified | Not bundled | **Unresolved upstream** |
| Oxford-IIIT Pet, Food-101, or similar | Upstream dataset pages | Student-selected 10-class subset | Upstream terms not verified | Not bundled | **Unresolved upstream** |
| Speech Commands | Upstream dataset page | Student-selected subset | Upstream terms not verified | Not bundled | **Unresolved upstream** |
| LibriSpeech | <https://www.openslr.org/12> | `dev-clean` subset | Course docs state CC BY 4.0; verify the exact release page | Not bundled | **Pending verification** |
| Common Voice | <https://commonvoice.mozilla.org/> | Language and version selected by the student | Course docs state CC0 1.0; speaker metadata still needs review | Not bundled | **Pending verification** |
| UCF101 | Upstream dataset page | Student-selected subset | Course docs describe it as commonly research-only | No redistribution without permission | **Unresolved upstream** |
| Student-supplied dataset | Student's source | Unknown | Student must record source, licence, consent, and redistribution rights | Not covered by the repository licence | **Student responsibility** |

## 3. Models and weights

| Model / artifact | Source | Exact version or artifact | Code licence | Weight terms | Bundled? | Status |
| --- | --- | --- | --- | --- | --- | --- |
| SSDLite320-MobileNetV3 COCO | torchvision | `ssdlite320_mobilenet_v3_large_coco-a79551df.pth`; `COCO_V1` / `DEFAULT` | BSD-3-Clause | **No separate weight licence stated**; may inherit COCO-derived terms | **No** | **Unresolved weights** |
| Fine-tuned SSDLite derivative (`TrafficSSDLite`) | Course training on synthetic video frames | Local checkpoint under ignored `projects/video-ai/outputs/` | Course code is MIT | May inherit the upstream SSDLite weight terms; review before distribution | **No** | **Unresolved derivative** |
| Optional torchvision ImageNet backbone | torchvision | Default `resnet18`; student may select another model | BSD-3-Clause | Model-specific ImageNet weight terms; not separately verified | **No** | **Unresolved weights** |
| SmolLM2-135M-Instruct | Hugging Face | `HuggingFaceTB/SmolLM2-135M-Instruct` | Upstream model repository terms | P03 describes it as Apache-2.0 "at the time of writing"; verify the exact revision and model card | **No** | **Pending verification** |
| SmolLM2-360M-Instruct | Hugging Face | `HuggingFaceTB/SmolLM2-360M-Instruct` (lesson example) | Upstream model repository terms | No licence claim is made by this repository; verify the exact revision | **No** | **Pending verification** |
| Qwen2.5-0.5B-Instruct | Hugging Face | `Qwen/Qwen2.5-0.5B-Instruct` | Upstream model repository terms | P03 describes it as Apache-2.0 "at the time of writing"; verify the exact revision and model card | **No** | **Pending verification** |
| Student-selected ASR or TTS model | Student's source | No model is pinned; Whisper and wav2vec2 are mentioned only as examples | Upstream terms | Upstream model and weight terms; consent and dataset terms also apply | **No** | **Unresolved upstream** |
| Course tiny models (`TinyCNN`, `TinyAudioCNN`, `TinyCRNN`, `TinyDetector`, `GarmentNet`, `TemporalClassifier`) | AITopics training code | Trained from scratch or from the course's synthetic backbone | MIT for original code | Original weights; no third-party pretrained inheritance | **No** | **Covered by repository code licence** |

### Attribution and notice obligations

No third-party dataset, weight file, or media asset is bundled, so this
repository does not ship an upstream notice bundle. When a student downloads or
uses one, they must retain the upstream citation and licence notice. In
particular:

- COCO: cite the COCO paper and dataset page; do not imply that the COCO
  Consortium owns or endorses the images;
- CIFAR-10, Fashion-MNIST, DeepFashion, TinyShakespeare, Speech Commands,
  LibriSpeech, Common Voice, and UCF101: follow the exact dataset card and
  citation requested by the selected release;
- SmolLM2, Qwen, torchvision, and ASR/TTS models: retain the model card and code
  notices; do not imply endorsement by the upstream authors;
- SSDLite: retain the torchvision BSD-3-Clause notice and cite COCO, while
  keeping the weight terms unresolved.

### SSDLite code-versus-weights distinction

The implementation in `torchvision.models.detection` is BSD-3-Clause. The COCO
weight file is a separate artifact. Torchvision says pretrained models "may have
their own licenses or terms and conditions derived from the dataset used for
training" and places responsibility for permission on the user. No separate
SSDLite weight licence is stated. Therefore:

- do **not** call the weights MIT, BSD-3-Clause, or CC BY 4.0;
- do **not** redistribute the `.pth` file or a fine-tuned derivative without a
  separate review;
- retain the torchvision BSD-3-Clause notice and cite COCO when discussing the
  model; attribution alone does not resolve the weight terms.

The repository's local ignored cache contains
`projects/video-ai/.cache/torch/hub/checkpoints/ssdlite320_mobilenet_v3_large_coco-a79551df.pth`
and a MobileNetV3 backbone file. Both are excluded by `**/.cache/` and are not
release files.

## 4. External code and media

| Category | Finding | Status |
| --- | --- | --- |
| Code blocks in lessons, labs, and notebooks | Written for the course or expressed from documented APIs; no copied-source notice found | **No copy identified; not a similarity audit** |
| Documentation diagrams | Authored in Markdown/Mermaid or generated by course code | **CC BY 4.0** |
| Generated charts and videos | Produced by course code from synthetic data | **CC0 1.0 where provenance is verified; otherwise review** |
| Third-party images, audio, video, quoted excerpts | No tracked third-party media found | **Verified none bundled** |
| Future contributor media | Not covered by this audit | **Requires source, licence, and attribution review** |

## 5. Optional dependencies

The full direct-dependency register, including licences and notice obligations,
is in [Licensing and attribution](licensing-and-attribution.md). The audited
local environment resolved: NumPy 2.5.4, pandas 2.3.3, scikit-learn 1.9.1,
SciPy 1.18.1, Pillow 13.0.0, PyTorch 2.7.1+cpu, OpenCV headless 5.0.0.93,
JupyterLab 4.6.5, ipykernel 6.31.0, nbclient 0.11.0, MkDocs 1.6.1, and Material
for MkDocs 9.8.0. `torchvision` and the optional LLM packages were not installed
in that environment. The requirement files use ranges; CI resolves a fresh set,
so the runner result is the release evidence.

These optional packages are not installed in the audited environment:

| Package | Declared in | Recorded licence | Additional issue | Status |
| --- | --- | --- | --- | --- |
| Streamlit | `requirements/llm.txt` | Apache-2.0 (verify the installed release) | None for the offline path | **Pending verification** |
| sentence-transformers | `requirements/llm.txt` | Apache-2.0 (verify the installed release) | Downloads model weights with their own terms | **Pending verification** |
| piper-tts | `requirements/audio.txt` comment | MIT for the package (verify) | Voice models have separate terms and are not bundled | **Pending verification** |

The audited environment does not contain `torchvision` or the optional LLM
packages. CI installs `requirements/ci.txt`; a developer who installs
`requirements/llm.txt` must check the package and model cards at the selected
versions.

## 6. Unresolved items and required actions

1. **SSDLite COCO weights.** Obtain authoritative terms or keep the artifacts
   unbundled and unresolved. Do not publish a fine-tuned checkpoint without a
   separate review.
2. **Optional torchvision ImageNet weights.** The optional transfer path can
   download weights whose terms are model-specific. Record the exact model and
   revision if a student uses it.
3. **SmolLM2, Qwen, and ASR/TTS models.** Record the exact model card, revision,
   licence URL, and weight hash before redistributing anything.
4. **External datasets.** COCO image-level terms, DeepFashion restrictions, and
   student-selected datasets remain upstream matters.
5. **Fine-tuned checkpoints.** A checkpoint derived from third-party weights may
   inherit restrictions; the repository licence does not resolve that.
6. **Media and code provenance.** No third-party media is bundled and no copied
   code was identified, but neither finding is a legal clearance or a
   code-similarity audit.
