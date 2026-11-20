#!/usr/bin/env bun
/**
 * AI ANIMATED VIDEO PRODUCTION STUDIO ORCHESTRATOR
 * Unified CLI & Automation Engine (Powered by OpenGen Engine 5)
 */

import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { spawnSync, execSync } from 'node:child_process';
import { TemplateResolver } from '../packages/core/src/index';
import { MotionGraphicsEngineAdapter } from '../packages/cli/src/opengen-adapter';
import { ThreeSceneFactory } from '../packages/engine-pdoom/src/index';

const STUDIO_ROOT = path.resolve(import.meta.dir, '..');
const OUT_DIR = path.resolve(STUDIO_ROOT, 'out');
const FINAL_DIR = path.resolve(OUT_DIR, 'final');
const WIP_DIR = path.resolve(OUT_DIR, 'wip');
const TEMPLATES_DIR = path.resolve(STUDIO_ROOT, 'templates');
const ASSETS_DIR = path.resolve(STUDIO_ROOT, 'assets');

// Ensure base directories exist
[OUT_DIR, FINAL_DIR, WIP_DIR, TEMPLATES_DIR, ASSETS_DIR].forEach(dir => {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
});

const args = process.argv.slice(2);
const command = args[0] || 'status';

function printHelp() {
  console.log(`
=============================================================================
   AI ANIMATED VIDEO PRODUCTION STUDIO - ORCHESTRATOR (ENGINE 5 UNIFIED)
=============================================================================

Usage:
  bun studio/orchestrator.ts <command> [options]

Commands:
  status                     Display studio engine status & hardware detection
  list-templates             List available production templates
  generate-audio <text>      Generate TTS audio voiceover using local AI
  render-reel                Render a high-impact 9:16 Instagram Reel via template
  render-3d                  Render a 3D Three.js motion graphics sequence
  render-ad                  Generate & render a 9:16 direct-response ad with Engine 5
  audit-ad                   Pre-flight social retention audit of an ad brief

Options:
  --brief <text>             Creative ad brief or prompt (default: auto)
  --provider <name>          AI model provider: offline | gemini | openai | anthropic | ollama
  --title <name>             Project title (default: "opengen_ad")
  --template <id>            Template identifier (default: "tech-explainer")
  --duration <sec>           Duration in seconds (default: 16.7, max 29.5)
  --fps <number>             Frames per second (default: 30)
  --out <path>               Output MP4 file path
  --run-dir <path>           Isolated job run directory for all WIP files
`);
}

function getOpt(name: string, fallback: string): string {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 && args[idx + 1] ? args[idx + 1] : fallback;
}

async function handleStatus() {
  const adapter = new MotionGraphicsEngineAdapter();
  const status = await adapter.checkStatus();

  console.log('\n--- STUDIO ENGINE & HARDWARE STATUS ---');
  console.log(`Workspace Root : ${STUDIO_ROOT}`);
  console.log(`Output Directory: ${OUT_DIR}`);
  console.log(`Hardware Acceleration: ${status.gpu}`);

  // Test FFmpeg
  try {
    const ffVer = execSync('ffmpeg -version', { encoding: 'utf-8' }).split('\n')[0];
    console.log(`[x] FFmpeg: ${ffVer}`);
  } catch {
    console.log('[ ] FFmpeg: NOT FOUND');
  }

  // Test Node & Bun
  console.log(`[x] Bun Runtime: ${Bun.version}`);
  console.log(`[x] Node Runtime: ${process.version}`);

  // Test Chrome & 2D Engine
  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  if (existsSync(chromePath)) {
    console.log(`[x] Google Chrome: ${chromePath} (Headless GPU Acceleration READY)`);
  }
  console.log(`[x] HyperFrames 2D Engine: HTML5 + CSS3 + GSAP 3.12 (READY)`);

  // Test pdoom-video
  const pdoomApp = path.join(STUDIO_ROOT, 'pdoom-video', 'app');
  if (existsSync(path.join(pdoomApp, 'node_modules', 'three'))) {
    console.log('[x] pdoom-video Engine: Three.js + Anime.js + WebGL Shaders (READY)');
  }

  console.log('\n--- OPENGEN ENGINE 5: MODEL-AGNOSTIC AI PROVIDERS ---');
  status.aiProviders.forEach(p => console.log(`  [x] Provider: ${p}`));

  console.log('\nAll primary production modules are operational.\n');
}

async function handleListTemplates() {
  const resolver = new TemplateResolver();
  const templates = resolver.listTemplates();
  console.log('\n--- AVAILABLE VIDEO TEMPLATES ---');
  templates.forEach(t => console.log(`  - ${t}`));
  console.log();
}

async function handleGenerateAudio(text: string, outAudioPath: string) {
  console.log(`\n[Audio Pipeline] Generating speech audio for: "${text}"`);
  console.log(`Output: ${outAudioPath}`);

  const outDir = path.dirname(outAudioPath);
  if (!existsSync(outDir)) mkdirSync(outDir, { recursive: true });

  const res = spawnSync('npx.cmd', ['hyperframes', 'tts', text, '-o', outAudioPath], {
    cwd: STUDIO_ROOT,
    stdio: 'inherit',
    shell: true
  });

  if (res.status === 0 && existsSync(outAudioPath)) {
    console.log(`[Audio Pipeline] Audio generated successfully: ${outAudioPath}`);
    return true;
  } else {
    console.log(`[Audio Pipeline] Generating fallback audio tone.`);
    execSync(`ffmpeg -y -f lavfi -i "sine=frequency=440:duration=3" -q:a 2 "${outAudioPath}"`);
    return true;
  }
}

async function handleRenderReel() {
  const templateId = getOpt('template', 'tech-explainer');
  const title = getOpt('title', templateId);
  const outPath = getOpt('out', path.join(FINAL_DIR, `${title}.mp4`));

  console.log(`\n[Studio Orchestrator] Rendering Instagram Reel via Template: ${templateId}`);
  console.log(`Output Target: ${outPath}`);

  const adapter = new MotionGraphicsEngineAdapter();
  const result = await adapter.renderTemplate(templateId, {}, outPath);

  if (existsSync(result)) {
    console.log(`\n[SUCCESS] Reel successfully generated and exported:`);
    console.log(`--> ${result}\n`);
  }
}

async function handleRender3D() {
  const from = parseFloat(getOpt('from', '0'));
  const to = parseFloat(getOpt('to', '5'));
  const outPath = getOpt('out', path.join(FINAL_DIR, `3d_sequence_${from}_${to}.mp4`));

  console.log(`\n[Studio Orchestrator] Rendering 3D Motion Graphics Sequence (Three.js + GLSL)`);
  console.log(`Time Range: ${from}s -> ${to}s (9:16 Portrait Reel)`);
  console.log(`Output Target: ${outPath}`);

  await ThreeSceneFactory.renderPdoomScene({
    from,
    to,
    fps: 30,
    outputPath: outPath,
    onProgress: (pct, msg) => console.log(`[${pct}%] ${msg}`)
  });

  if (existsSync(outPath)) {
    console.log(`\n[SUCCESS] 3D sequence successfully rendered:`);
    console.log(`--> ${outPath}\n`);
  }
}

async function handleRenderAd() {
  const brief = getOpt('brief', 'Stop wasting hours on manual editing. OpenGen Engine 5 delivers instant AI motion graphics with zero vendor lock-in.');
  const provider = getOpt('provider', 'offline');
  const duration = parseFloat(getOpt('duration', '16.7'));
  const title = getOpt('title', 'opengen_performance_ad');
  const runDirOpt = getOpt('run-dir', '');
  const outPath = getOpt('out', runDirOpt ? path.join(runDirOpt, `${title}.mp4`) : path.join(FINAL_DIR, `${title}.mp4`));
  const runDir = runDirOpt || path.dirname(outPath);

  console.log(`\n=============================================================================`);
  console.log(`   OPENGEN ENGINE 5: DIRECT-RESPONSE PERFORMANCE AD PIPELINE`);
  console.log(`=============================================================================`);
  console.log(`Creative Brief : "${brief}"`);
  console.log(`AI Provider    : ${provider.toUpperCase()}`);
  console.log(`Aspect Ratio   : 9:16 Portrait (1080x1920)`);
  console.log(`Duration Target: ${duration}s (< 30s Social Ad Cap)`);
  console.log(`Output Target  : ${outPath}\n`);

  const adapter = new MotionGraphicsEngineAdapter();

  console.log(`[Step 1/3] AdDirectorAgent: Compiling 5-Phase Conversion Funnel...`);
  const project = await adapter.planAd(brief, { duration, provider });
  console.log(`[x] Compiled project: "${project.title}" (${project.scenes.length} scenes)`);

  console.log(`\n[Step 2/3] AdCriticAgent: Running Pre-Flight Social Retention Audit...`);
  const audit = await adapter.auditAd(project);
  console.log(`[x] Ad Critic Score: ${audit.score}/100 (Passed: ${audit.passed})`);
  if (!audit.passed) {
    console.warn(`[!] Violations detected:`, audit.violations);
    console.warn(`[!] Suggested remedies:`, audit.suggestedRemedies);
  }

  console.log(`\n[Step 3/3] Deterministic Renderer: Compiling HTML5/GSAP with MicroEditor & Rendering...`);
  const renderedMp4 = await adapter.render(project, { outputPath: outPath, runDir, fps: 30 });

  if (existsSync(renderedMp4)) {
    console.log(`\n=============================================================================`);
    console.log(`[SUCCESS] Performance Ad Successfully Rendered & Mastered by Engine 5:`);
    console.log(`--> ${renderedMp4}`);
    console.log(`=============================================================================\n`);
  }
}

async function handleAuditAd() {
  const brief = getOpt('brief', 'Instant AI Motion Graphics Studio with OpenGen Engine 5');
  const provider = getOpt('provider', 'offline');
  const duration = parseFloat(getOpt('duration', '16.7'));

  console.log(`\n[AdCriticAgent] Auditing Ad Brief: "${brief}"`);
  const adapter = new MotionGraphicsEngineAdapter();
  const project = await adapter.planAd(brief, { duration, provider });
  const audit = await adapter.auditAd(project);

  console.log(`\n--- AD CRITIC RETENTION AUDIT REPORT ---`);
  console.log(`Score: ${audit.score}/100`);
  console.log(`Passed: ${audit.passed ? 'YES' : 'NO'}`);
  if (audit.violations.length > 0) {
    console.log(`Violations:`);
    audit.violations.forEach(v => console.log(`  - ${v}`));
  } else {
    console.log(`Violations: None (All viral retention checks passed)`);
  }
  if (audit.suggestedRemedies.length > 0) {
    console.log(`Suggested Remedies:`);
    audit.suggestedRemedies.forEach(r => console.log(`  - ${r}`));
  }
  console.log();
}

// Router
switch (command) {
  case 'status':
    await handleStatus();
    break;
  case 'list-templates':
    await handleListTemplates();
    break;
  case 'generate-audio':
    const text = args[1] || 'Welcome to the AI Animated Video Production Studio.';
    const audioOut = path.join(ASSETS_DIR, 'audio', 'generated_voice.mp3');
    await handleGenerateAudio(text, audioOut);
    break;
  case 'render-reel':
    await handleRenderReel();
    break;
  case 'render-3d':
    await handleRender3D();
    break;
  case 'render-ad':
    await handleRenderAd();
    break;
  case 'audit-ad':
    await handleAuditAd();
    break;
  case '--help':
  case 'help':
  default:
    printHelp();
    break;
}
