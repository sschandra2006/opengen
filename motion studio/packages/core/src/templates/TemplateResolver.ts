import { OpenGenProject, AspectRatio } from '../types/ir';
import * as fs from 'node:fs';
import * as path from 'node:path';

export interface TemplateMetadata {
  id: string;
  name: string;
  category: string;
  supportedAspectRatios: AspectRatio[];
  defaultDuration: number;
  variables: Record<string, {
    type: 'string' | 'color' | 'number' | 'image' | 'audio' | 'font';
    default: any;
    label?: string;
    description?: string;
  }>;
  projectBlueprint: Record<string, any>;
}

export class TemplateResolver {
  private templatesDir: string;

  constructor(templatesDir?: string) {
    this.templatesDir = templatesDir || path.resolve(process.cwd(), 'templates');
  }

  public listTemplates(): string[] {
    if (!fs.existsSync(this.templatesDir)) return [];
    return fs.readdirSync(this.templatesDir, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);
  }

  public loadTemplate(templateId: string): TemplateMetadata {
    const templatePath = path.join(this.templatesDir, templateId, 'template.json');
    if (!fs.existsSync(templatePath)) {
      throw new Error(`Template not found at: ${templatePath}`);
    }
    const raw = fs.readFileSync(templatePath, 'utf-8');
    return JSON.parse(raw) as TemplateMetadata;
  }

  public hydrate(
    template: TemplateMetadata,
    variables: Record<string, any> = {},
    options: { aspectRatio?: AspectRatio; duration?: number } = {}
  ): OpenGenProject {
    const aspectRatio = options.aspectRatio || template.supportedAspectRatios[0] || '9:16';
    const duration = options.duration || template.defaultDuration || 15.0;

    let width = 1080;
    let height = 1920;
    if (aspectRatio === '16:9') {
      width = 1920;
      height = 1080;
    } else if (aspectRatio === '1:1') {
      width = 1080;
      height = 1080;
    } else if (aspectRatio === '4:5') {
      width = 1080;
      height = 1350;
    }

    // Merge default variables with user variables
    const resolvedVars: Record<string, any> = {
      aspect_width: width,
      aspect_height: height,
      aspect_ratio: aspectRatio,
      duration: duration,
      generated_id: `proj_${Date.now()}`
    };

    if (template.variables) {
      for (const [key, def] of Object.entries(template.variables)) {
        resolvedVars[key] = variables[key] !== undefined ? variables[key] : def.default;
      }
    }

    // Deep string substitution in blueprint JSON
    let blueprintStr = JSON.stringify(template.projectBlueprint);
    for (const [key, val] of Object.entries(resolvedVars)) {
      const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
      blueprintStr = blueprintStr.replace(regex, String(val));
    }

    const hydratedProject = JSON.parse(blueprintStr) as OpenGenProject;
    hydratedProject.settings.width = width;
    hydratedProject.settings.height = height;
    hydratedProject.settings.aspectRatio = aspectRatio;
    hydratedProject.settings.duration = duration;

    return hydratedProject;
  }
}
