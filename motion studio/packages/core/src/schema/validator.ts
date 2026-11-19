import { OpenGenProject, Scene, Layer, Animation, AudioTrack } from '../types/ir';
import * as fs from 'node:fs';
import * as path from 'node:path';

export interface ValidationError {
  path: string;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

export class ProjectValidator {
  public static validate(project: unknown): ValidationResult {
    const errors: ValidationError[] = [];

    if (!project || typeof project !== 'object') {
      return { valid: false, errors: [{ path: '', message: 'Project must be a non-null object' }] };
    }

    const p = project as Partial<OpenGenProject>;

    // 1. Required top-level fields
    if (!p.schemaVersion || !['1.0.0', '1.1.0'].includes(p.schemaVersion)) {
      errors.push({ path: 'schemaVersion', message: 'schemaVersion must be "1.0.0" or "1.1.0"' });
    }

    if (!p.projectId || typeof p.projectId !== 'string') {
      errors.push({ path: 'projectId', message: 'projectId is required and must be a string' });
    } else if (!/^[a-zA-Z0-9_-]+$/.test(p.projectId)) {
      errors.push({ path: 'projectId', message: 'projectId must contain only alphanumeric characters, dashes, or underscores' });
    }

    if (!p.title || typeof p.title !== 'string') {
      errors.push({ path: 'title', message: 'title is required and must be a string' });
    }

    // 2. Settings validation
    if (!p.settings || typeof p.settings !== 'object') {
      errors.push({ path: 'settings', message: 'settings object is required' });
    } else {
      const s = p.settings;
      if (!s.width || typeof s.width !== 'number' || s.width <= 0) {
        errors.push({ path: 'settings.width', message: 'width must be a positive integer' });
      }
      if (!s.height || typeof s.height !== 'number' || s.height <= 0) {
        errors.push({ path: 'settings.height', message: 'height must be a positive integer' });
      }
      if (!s.fps || ![24, 25, 30, 50, 60].includes(s.fps)) {
        errors.push({ path: 'settings.fps', message: 'fps must be 24, 25, 30, 50, or 60' });
      }
      if (!s.aspectRatio || !['16:9', '9:16', '1:1', '4:5'].includes(s.aspectRatio)) {
        errors.push({ path: 'settings.aspectRatio', message: 'aspectRatio must be 16:9, 9:16, 1:1, or 4:5' });
      }
      if (typeof s.duration !== 'number' || s.duration <= 0) {
        errors.push({ path: 'settings.duration', message: 'duration must be a positive number' });
      }
    }

    // 3. Scenes validation
    if (!Array.isArray(p.scenes) || p.scenes.length === 0) {
      errors.push({ path: 'scenes', message: 'scenes must be a non-empty array' });
    } else {
      let cumulativeTime = 0;
      p.scenes.forEach((scene, sIdx) => {
        const scenePath = `scenes[${sIdx}]`;

        if (!scene.id || typeof scene.id !== 'string') {
          errors.push({ path: `${scenePath}.id`, message: 'scene id is required' });
        }
        if (typeof scene.start !== 'number' || scene.start < 0) {
          errors.push({ path: `${scenePath}.start`, message: 'scene start must be >= 0' });
        }
        if (typeof scene.duration !== 'number' || scene.duration <= 0) {
          errors.push({ path: `${scenePath}.duration`, message: 'scene duration must be > 0' });
        }

        cumulativeTime += scene.duration || 0;

        // Validate layers
        if (!Array.isArray(scene.layers)) {
          errors.push({ path: `${scenePath}.layers`, message: 'layers must be an array' });
        } else {
          scene.layers.forEach((layer, lIdx) => {
            const layerPath = `${scenePath}.layers[${lIdx}]`;
            if (!layer.id) {
              errors.push({ path: `${layerPath}.id`, message: 'layer id is required' });
            }
            if (!layer.type) {
              errors.push({ path: `${layerPath}.type`, message: 'layer type is required' });
            }
            if (typeof layer.start !== 'number' || layer.start < 0) {
              errors.push({ path: `${layerPath}.start`, message: 'layer start must be >= 0' });
            }
            if (typeof layer.duration !== 'number' || layer.duration <= 0) {
              errors.push({ path: `${layerPath}.duration`, message: 'layer duration must be > 0' });
            }

            // Validate animations
            if (layer.animations && Array.isArray(layer.animations)) {
              layer.animations.forEach((anim, aIdx) => {
                const animPath = `${layerPath}.animations[${aIdx}]`;
                if (!anim.property) {
                  errors.push({ path: `${animPath}.property`, message: 'animation property is required' });
                }
                if (typeof anim.duration !== 'number' || anim.duration <= 0) {
                  errors.push({ path: `${animPath}.duration`, message: 'animation duration must be > 0' });
                }
              });
            }
          });
        }
      });

      if (p.settings && p.settings.duration && Math.abs(cumulativeTime - p.settings.duration) > 0.5) {
        errors.push({
          path: 'scenes',
          message: `Cumulative scene duration (${cumulativeTime.toFixed(2)}s) does not match project duration (${p.settings.duration}s)`
        });
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}
