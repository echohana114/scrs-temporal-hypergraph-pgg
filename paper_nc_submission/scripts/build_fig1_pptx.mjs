import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "/Users/hui/Documents/演化博弈-NC";
const skillDir = "/Users/hui/.codex/plugins/cache/openai-primary-runtime/presentations/26.923.10815/skills/presentations";
const runtimePython = "/Users/hui/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";
const tmpDir = path.join(workspaceDir, "paper_nc_submission", ".pptx_build", "fig1_groupcards");
const outputDir = path.join(workspaceDir, "paper_nc_submission", "dist");
const finalPptx = path.join(outputDir, "fig1_model_diagram_groupcards_20260926_154320.pptx");
const sourceSvg = path.join(workspaceDir, "paper_nc_submission", "figures", "fig1_model_diagram.svg");

const { finalizePresentation } = await import(
  pathToFileURL(path.join(skillDir, "container_tools", "artifact_tool_utils.mjs")).href,
);

await fs.mkdir(tmpDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

const svgBytes = await fs.readFile(sourceSvg);
const presentation = Presentation.create({
  slideSize: { width: 1280, height: 720 },
});

const slide = presentation.slides.add();
slide.background.fill = "#FFFFFF";
slide.images.add({
  blob: svgBytes,
  contentType: "image/svg+xml",
  alt: "Figure 1. SCRS temporal-hypergraph system architecture",
  fit: "contain",
  position: { left: 0, top: 0, width: 1280, height: 720 },
});
slide.speakerNotes.textFrame.setText(
  "Source figure: paper_nc_submission/figures/fig1_model_diagram.svg. The slide preserves the figure as a full-slide vector image for PowerPoint review and annotation.",
);

const candidatePath = path.join(tmpDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const draftPreview = await presentation.export({ slide, format: "png", scale: 1.25 });
await fs.writeFile(path.join(tmpDir, "fig1_pptx_preview.png"), new Uint8Array(await draftPreview.arrayBuffer()));

await finalizePresentation({
  explicitTotalSlideCount: 1,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  workspaceDir,
  candidatePath,
  finalPath: finalPptx,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu",
    "12192000,6858000",
    "--validate-heading-fit",
    "--validate-bullet-geometry",
  ],
  fontPolicy: { basis: "design", families: ["Arial", "Helvetica"] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(tmpDir, "fig1_model_diagram_groupcards_20260926_154320.validation.json"),
});

console.log(finalPptx);
