import { OpenGenProject, AspectRatio } from '@opengen/core';
import { RenderJobRunner } from '@opengen/renderer';
import { TemplateResolver } from '@opengen/core';
import { execSync, spawnSync } from 'node:child_process';
import * as path from 'node:path';
import * as fs from 'node:fs';

export interface Engine5Status {
  operational: boolean;
  gpu: string;
  engines: string[];
  aiProviders: string[];
}

export interface AdCriticResult {
  passed: boolean;
  score: number;
  violations: string[];
  suggestedRemedies: string[];
}

export interface OpenGenEngine5Plugin {
  readonly engineId: 'engine_5_motion_graphics';
  readonly name: 'OpenGen Motion Graphics Studio';
  readonly version: '1.1.0';

  /** Check engine health, hardware acceleration, and AI provider readiness */
  checkStatus(): Promise<Engine5Status>;

  /** Render project IR directly to MP4 */
  render(project: OpenGenProject, options?: { outputPath?: string; runDir?: string; fps?: number }): Promise<string>;

  /** Execute a pre-packaged template with hydrated variables */
  renderTemplate(templateId: string, variables: Record<string, any>, outputPath?: string): Promise<string>;

  /** Plan a high-converting performance ad using model-agnostic AI */
  planAd(brief: string, options?: { duration?: number; provider?: string }): Promise<OpenGenProject>;

  /** Run pre-flight quality audit on an ad project */
  auditAd(project: OpenGenProject): Promise<AdCriticResult>;
}

export class MotionGraphicsEngineAdapter implements OpenGenEngine5Plugin {
  public readonly engineId = 'engine_5_motion_graphics' as const;
  public readonly name = 'OpenGen Motion Graphics Studio' as const;
  public readonly version = '1.1.0' as const;

  private runner: RenderJobRunner;
  private templateResolver: TemplateResolver;

  constructor() {
    this.runner = new RenderJobRunner();
    this.templateResolver = new TemplateResolver();
  }

  public async checkStatus(): Promise<Engine5Status> {
    let gpu = 'CPU Software Fallback';
    try {
      const encoders = execSync('ffmpeg -encoders', { encoding: 'utf-8' });
      if (encoders.includes('h264_nvenc')) {
        gpu = 'NVIDIA NVENC Hardware Acceleration';
      } else if (encoders.includes('h264_qsv')) {
        gpu = 'Intel QuickSync Hardware Acceleration';
      }
    } catch {}

    const providers = ['offline (deterministic)'];
    if (process.env.GEMINI_API_KEY) providers.push('gemini');
    if (process.env.OPENAI_API_KEY) providers.push('openai');
    if (process.env.ANTHROPIC_API_KEY) providers.push('anthropic');
    if (process.env.OLLAMA_HOST || process.env.OLLAMA_MODEL) providers.push('ollama');

    return {
      operational: true,
      gpu,
      engines: [
        'hyperframes (Engine 1: 2D/GSAP)',
        'pdoom-video (Engine 2: 3D/Three.js/GLSL)',
        'VoiceStudio (Engine 3: Kokoro/Whisper)',
        'raea (Engine 4: Bevy/WGPU Quality Gate)'
      ],
      aiProviders: providers
    };
  }

  public async render(project: OpenGenProject, options?: { outputPath?: string; runDir?: string; fps?: number }): Promise<string> {
    return this.runner.renderProject(project, options);
  }

  public async renderTemplate(templateId: string, variables: Record<string, any> = {}, outputPath?: string): Promise<string> {
    const template = this.templateResolver.loadTemplate(templateId);
    const project = this.templateResolver.hydrate(template, variables);
    return this.runner.renderProject(project, { outputPath });
  }

  public async planAd(brief: string, options: { duration?: number; provider?: string } = {}): Promise<OpenGenProject> {
    const duration = options.duration || 18.0;
    const providerArg = options.provider ? `provider_name='${options.provider}'` : '';
    const script = `
import sys, json
sys.path.insert(0, 'python')
from opengen.creative import AdDirectorAgent
from opengen.ai.providers import AIProviderFactory
provider = AIProviderFactory.get_provider(${providerArg})
director = AdDirectorAgent(provider=provider, target_duration=${duration})
plan = director.build_creative_ad_plan('''${brief.replace(/'/g, "\\'")}''')
print("JSON_START")
print(json.dumps(plan))
print("JSON_END")
`;
    const res = spawnSync('python', ['-c', script], { encoding: 'utf-8' });
    if (res.status !== 0) {
      throw new Error(`Failed to plan ad: ${res.stderr || res.stdout}`);
    }
    const match = res.stdout.match(/JSON_START\s*([\s\S]*?)\s*JSON_END/);
    if (!match) {
      throw new Error(`Failed to extract JSON from ad planner output: ${res.stdout}`);
    }
    return JSON.parse(match[1]) as OpenGenProject;
  }

  public async auditAd(project: OpenGenProject): Promise<AdCriticResult> {
    const tempFile = path.resolve('out', 'wip', `audit_${Date.now()}.json`);
    fs.mkdirSync(path.dirname(tempFile), { recursive: true });
    fs.writeFileSync(tempFile, JSON.stringify(project, null, 2), 'utf-8');

    const script = `
import sys, json
sys.path.insert(0, 'python')
from opengen.creative import AdCriticAgent
with open(r'''${tempFile}''', 'r', encoding='utf-8') as f:
    ir = json.load(f)
critic = AdCriticAgent()
report = critic.audit_ad_timeline(ir)
print("AUDIT_START")
print(json.dumps(report))
print("AUDIT_END")
`;
    const res = spawnSync('python', ['-c', script], { encoding: 'utf-8' });
    try { fs.unlinkSync(tempFile); } catch {}

    if (res.status !== 0) {
      throw new Error(`Audit failed: ${res.stderr || res.stdout}`);
    }
    const match = res.stdout.match(/AUDIT_START\s*([\s\S]*?)\s*AUDIT_END/);
    if (!match) {
      throw new Error(`Failed to parse audit report: ${res.stdout}`);
    }
    return JSON.parse(match[1]) as AdCriticResult;
  }
}
