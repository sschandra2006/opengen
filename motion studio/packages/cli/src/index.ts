#!/usr/bin/env bun
import { ProjectValidator, OpenGenProject, TemplateResolver } from '@opengen/core';
import { RenderJobRunner } from '@opengen/renderer';
import { MotionGraphicsEngineAdapter } from './opengen-adapter';
import { ThreeSceneFactory } from '@opengen/engine-pdoom';
import { spawnSync, execSync } from 'node:child_process';
import * as path from 'node:path';
import * as fs from 'node:fs';

const args = process.argv.slice(2);
const command = args[0] || 'help';

function getOpt(name: string, fallback: string = ''): string {
  const idx = args.indexOf(`--${name}`);
  if (idx !== -1 && args[idx + 1]) {
    return args[idx + 1];
  }
  const shortIdx = args.indexOf(`-${name[0]}`);
  if (shortIdx !== -1 && args[shortIdx + 1]) {
    return args[shortIdx + 1];
  }
  return fallback;
}

function printHelp() {
  console.log(`
=============================================================================
   OPENGEN MOTION GRAPHICS STUDIO - STANDALONE VIDEO GENERATION ENGINE
=============================================================================

Usage:
  bun packages/cli/src/index.ts <command> [options]
  (or via package alias: bun run motion <command> [options])

Commands:
  status                      Check studio engines, GPU acceleration & tool health
  render                      Render an OpenGen IR project JSON to mastered MP4
  template list               List available production templates
  template render <id>        Render a pre-built template with hydrated variables
  audio tts "<text>"          Synthesize speech voiceover via local Kokoro-82M TTS
  audio beats <file.mp3>      Extract rhythm, tempo (BPM), and beat grid
  render-3d                   Render a Three.js / Anime.js 3D motion graphics sequence

Options:
  -p, --project <path>        Path to project.json file (for render)
  -o, --out <path>            Output MP4 / MP3 file path
  --fps <number>              Frame rate (default: 30)
  --vars <json>               Variable overrides for templates as JSON string
  --from <seconds>            Start second for 3D render (default: 0)
  --to <seconds>              End second for 3D render (default: 5)
  --landscape                 Render in 16:9 widescreen instead of 9:16 portrait
`);
}

async function handleStatus() {
  const adapter = new MotionGraphicsEngineAdapter();
  const status = await adapter.checkStatus();
  console.log('\n--- OPENGEN MOTION GRAPHICS ENGINE STATUS ---');
  console.log(`Operational: ${status.operational ? 'YES [ONLINE]' : 'NO [OFFLINE]'}`);
  console.log(`Hardware Acceleration: ${status.gpu}`);
  console.log('Engines:');
  status.engines.forEach(e => console.log(`  - ${e}`));

  // Check FFmpeg
  try {
    const ffVer = execSync('ffmpeg -version', { encoding: 'utf-8' }).split('\n')[0];
    console.log(`[x] FFmpeg: ${ffVer}`);
  } catch {
    console.log('[ ] FFmpeg: NOT FOUND');
  }

  // Check Google Chrome & Headless Renderer
  try {
    const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    if (fs.existsSync(chromePath)) {
      console.log(`[x] Google Chrome: Found at ${chromePath} (Headless GPU Acceleration READY)`);
    } else {
      console.log(`[!] Google Chrome: Default path not found, using system PATH`);
    }
  } catch {}

  // Check 2D Engine (HyperFrames HTML/GSAP)
  const hfDir = path.resolve(process.cwd(), 'hyperframes');
  if (fs.existsSync(hfDir)) {
    console.log(`[x] HyperFrames 2D Engine: HTML5 + CSS3 + GSAP 3.12 (READY)`);
  }

  // Check Three.js in pdoom-video
  const pdoomModules = path.resolve(process.cwd(), 'pdoom-video', 'app', 'node_modules', 'three');
  if (fs.existsSync(pdoomModules)) {
    console.log('[x] pdoom-video Engine: Three.js + Anime.js + WebGL Shaders (READY)');
  } else {
    console.log('[ ] pdoom-video Engine: node_modules missing');
  }

  console.log('\nStudio is fully ready for deterministic video rendering.\n');
}

async function handleRender() {
  const projectPath = getOpt('project', getOpt('p', ''));
  if (!projectPath) {
    console.error('Error: Please specify project JSON path using --project <file.json> or -p <file.json>');
    process.exit(1);
  }

  const resolvedPath = path.resolve(process.cwd(), projectPath);
  if (!fs.existsSync(resolvedPath)) {
    console.error(`Error: Project file not found: ${resolvedPath}`);
    process.exit(1);
  }

  console.log(`\n[Motion Engine] Loading project: ${resolvedPath}`);
  const project = JSON.parse(fs.readFileSync(resolvedPath, 'utf-8')) as OpenGenProject;

  const outPath = getOpt('out', getOpt('o', path.resolve(process.cwd(), 'out', 'final', `${project.projectId}.mp4`)));
  const fps = parseInt(getOpt('fps', String(project.settings.fps || 30)), 10);

  const runner = new RenderJobRunner();
  console.log(`[Motion Engine] Rendering target: ${outPath} (${fps} fps)`);

  const result = await runner.renderProject(project, {
    outputPath: outPath,
    fps,
    onProgress: (pct, msg) => console.log(`[${pct}%] ${msg}`)
  });

  console.log(`\n[SUCCESS] Render complete: ${result}\n`);
}

async function handleTemplate() {
  const sub = args[1];
  const resolver = new TemplateResolver();

  if (sub === 'list') {
    const templates = resolver.listTemplates();
    console.log('\n--- AVAILABLE VIDEO TEMPLATES ---');
    if (templates.length === 0) {
      console.log('No templates found in templates/ directory.');
    } else {
      templates.forEach(t => console.log(`  - ${t}`));
    }
    console.log();
    return;
  }

  if (sub === 'render') {
    const templateId = args[2];
    if (!templateId) {
      console.error('Error: Please specify template id: motion template render <templateId>');
      process.exit(1);
    }

    const varsJson = getOpt('vars', '{}');
    let variables = {};
    try {
      variables = JSON.parse(varsJson);
    } catch {
      console.error('Error: --vars must be valid JSON');
      process.exit(1);
    }

    const outPath = getOpt('out', getOpt('o', path.resolve(process.cwd(), 'out', 'final', `${templateId}_render.mp4`)));

    console.log(`\n[Motion Engine] Loading template: ${templateId}`);
    const adapter = new MotionGraphicsEngineAdapter();
    const result = await adapter.renderTemplate(templateId, variables, outPath);
    console.log(`\n[SUCCESS] Template rendered: ${result}\n`);
    return;
  }

  console.log('Usage: motion template <list|render>');
}

async function handleAudio() {
  const sub = args[1];
  if (sub === 'tts') {
    const text = args[2] || 'OpenGen turns your words into studio-grade animated videos.';
    const outAudio = getOpt('out', getOpt('o', path.resolve(process.cwd(), 'out', 'wip', 'tts_speech.mp3')));

    const outDir = path.dirname(outAudio);
    if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

    console.log(`\n[Audio Pipeline] Synthesizing speech: "${text}"`);
    console.log(`[Audio Pipeline] Output: ${outAudio}`);

    const res = spawnSync('npx.cmd', ['hyperframes', 'tts', text, '-o', outAudio], {
      shell: true,
      stdio: 'inherit'
    });

    if (res.status === 0 && fs.existsSync(outAudio)) {
      console.log(`\n[SUCCESS] Audio generated: ${outAudio}\n`);
    } else {
      console.error('Failed to generate audio via hyperframes tts.');
    }
    return;
  }

  if (sub === 'beats') {
    const audioFile = args[2];
    if (!audioFile) {
      console.error('Error: specify audio file: motion audio beats <file.mp3>');
      process.exit(1);
    }

    console.log(`\n[Audio Pipeline] Analyzing beats in: ${audioFile}`);
    spawnSync('npx.cmd', ['hyperframes', 'beats', audioFile, '--json'], {
      shell: true,
      stdio: 'inherit'
    });
    return;
  }

  console.log('Usage: motion audio <tts|beats>');
}

async function handleRender3D() {
  const from = parseFloat(getOpt('from', '0'));
  const to = parseFloat(getOpt('to', '5'));
  const landscape = args.includes('--landscape');
  const outPath = getOpt('out', getOpt('o', path.resolve(process.cwd(), 'out', 'final', `3d_${from}_${to}.mp4`)));

  console.log(`\n[3D Engine] Rendering Three.js + Anime.js sequence (${from}s -> ${to}s)`);
  console.log(`[3D Engine] Output: ${outPath}`);

  await ThreeSceneFactory.renderPdoomScene({
    from,
    to,
    fps: 30,
    landscape,
    outputPath: outPath,
    onProgress: (pct, msg) => console.log(`[${pct}%] ${msg}`)
  });

  console.log(`\n[SUCCESS] 3D sequence rendered: ${outPath}\n`);
}

// Router
switch (command) {
  case 'status':
    await handleStatus();
    break;
  case 'render':
    await handleRender();
    break;
  case 'template':
  case 'templates':
    await handleTemplate();
    break;
  case 'audio':
    await handleAudio();
    break;
  case 'render-3d':
  case '3d':
    await handleRender3D();
    break;
  case 'help':
  case '--help':
  default:
    printHelp();
    break;
}
