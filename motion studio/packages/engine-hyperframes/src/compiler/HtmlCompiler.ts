import { OpenGenProject, Scene, Layer, Animation } from '@opengen/core';
import { GsapTweenMapper } from './GsapTweenMapper';
import { MicroEditor } from './MicroEditor';
import * as fs from 'node:fs';
import * as path from 'node:path';

export class HtmlCompiler {
  public static compileToHtml(project: OpenGenProject, outputPath: string): string {
    const { width, height, fps, duration, backgroundColor } = project.settings;

    const scenesHtml = project.scenes.map((scene) => this.renderScene(scene, width, height)).join('\n');
    const timelinesJs = project.scenes.map((scene) => this.renderSceneTimeline(scene)).join('\n');

    const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${project.title}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: ${backgroundColor || '#000000'};
      width: ${width}px;
      height: ${height}px;
      overflow: hidden;
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      margin: 0;
      padding: 0;
    }
    #composition {
      position: relative;
      width: ${width}px;
      height: ${height}px;
      background-color: ${backgroundColor || '#000000'};
      overflow: hidden;
    }
    .clip {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      overflow: hidden;
      opacity: 0;
      pointer-events: none;
    }
    .clip.active {
      opacity: 1;
      pointer-events: auto;
    }
    .layer {
      position: absolute;
      display: flex;
      align-items: center;
      justify-content: center;
      will-change: transform, opacity;
      top: 0; left: 0;
      width: 100%; height: 100%;
    }
    .kinetic-word {
      display: inline-block;
      opacity: 0;
      transform: translateY(20px);
      margin: 0 4px;
    }
  </style>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
</head>
<body>
  <div id="composition" class="composition" data-fps="${fps}" data-duration="${duration}">
    ${scenesHtml}
  </div>

  <script>
    window.__READY__ = true;
    window.__timelines = window.__timelines || {};
    window.__scenes = ${JSON.stringify(project.scenes.map(s => ({ id: s.id, start: s.start, duration: s.duration })))};

    ${timelinesJs}

    // Deterministic seek function called by headless renderer
    window.__seek = function(t, frame) {
      for (const scene of window.__scenes) {
        const el = document.getElementById(scene.id);
        const tl = window.__timelines[scene.id];
        const sceneStart = scene.start;
        const sceneEnd = scene.start + scene.duration;

        if (t >= sceneStart && t < sceneEnd) {
          if (el && !el.classList.contains('active')) {
            el.classList.add('active');
          }
          if (tl) {
            tl.seek(t - sceneStart, false);
          }
        } else {
          if (el && el.classList.contains('active')) {
            el.classList.remove('active');
          }
        }
      }
    };

    // Initialize at t = 0
    window.__seek(0, 0);
  </script>
</body>
</html>`;

    const outDir = path.dirname(outputPath);
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, htmlContent, 'utf-8');
    return outputPath;
  }

  private static renderScene(scene: Scene, width: number, height: number): string {
    const layersHtml = scene.layers.map((layer) => this.renderLayer(layer, width, height)).join('\n      ');
    const bgStyle = scene.backgroundColor ? `background-color: ${scene.backgroundColor};` : '';
    return `    <div class="clip" id="${scene.id}" data-start="${scene.start}" data-duration="${scene.duration}" style="${bgStyle}">
      ${layersHtml}
    </div>`;
  }

  private static renderLayer(layer: Layer, width: number, height: number): string {
    const { id, type, transform, content, zIndex } = layer;
    
    // Transform CSS
    let transformCss = '';
    const tx = transform?.x ?? 0;
    const ty = transform?.y ?? 0;
    const tz = transform?.z ?? 0;
    const scaleX = transform?.scaleX ?? transform?.scale ?? 1;
    const scaleY = transform?.scaleY ?? transform?.scale ?? 1;
    const rot = transform?.rotation ?? 0;

    transformCss = `transform: translate3d(${tx}px, ${ty}px, ${tz}px) scale(${scaleX}, ${scaleY}) rotate(${rot}deg);`;
    const opacityCss = `opacity: ${transform?.opacity ?? 1};`;
    const zIndexCss = `z-index: ${zIndex ?? 1};`;
    const style = `${zIndexCss} ${opacityCss} ${transformCss}`;

    if (type === 'text') {
      const tc = content || {};
      const fontSize = tc.fontSize || 48;
      const color = tc.color || '#ffffff';
      const fontWeight = tc.fontWeight || 800;
      const textAlign = tc.textAlign || 'center';
      const letterSpacing = tc.letterSpacing ? `letter-spacing: ${tc.letterSpacing}px;` : '';
      const textTransform = tc.textTransform ? `text-transform: ${tc.textTransform};` : '';

      if (tc.kineticMode === 'word-by-word') {
        const words = (tc.text || '').split(' ');
        const wordSpans = words.map((w: string, idx: number) => 
          `<span class="kinetic-word kw_${id}" id="${id}_w${idx}">${w}</span>`
        ).join(' ');

        return `<div id="${id}" class="layer" style="${style}">
          <div style="font-size: ${fontSize}px; color: ${color}; font-weight: ${fontWeight}; text-align: ${textAlign}; width: 85%; line-height: 1.2; ${letterSpacing} ${textTransform}">
            ${wordSpans}
          </div>
        </div>`;
      }

      return `<div id="${id}" class="layer" style="${style}">
        <div style="font-size: ${fontSize}px; color: ${color}; font-weight: ${fontWeight}; text-align: ${textAlign}; width: 85%; line-height: 1.2; ${letterSpacing} ${textTransform}">
          ${tc.text || ''}
        </div>
      </div>`;
    }

    if (type === 'image') {
      const ic = content || {};
      return `<div id="${id}" class="layer" style="${style}">
        <img src="${ic.src || ''}" style="width: 100%; height: 100%; object-fit: ${ic.fit || 'contain'}; border-radius: ${ic.borderRadius || 0}px;" />
      </div>`;
    }

    if (type === 'chart') {
      const cc = content || {};
      if (cc.chartType === 'counter') {
        const targetVal = cc.chartData?.targetValue ?? 100;
        const prefix = cc.chartData?.prefix ?? '';
        const suffix = cc.chartData?.suffix ?? '';
        return `<div id="${id}" class="layer" style="${style}">
          <div style="font-size: ${cc.fontSize || 72}px; font-weight: ${cc.fontWeight || 900}; color: ${cc.color || '#38bdf8'}; font-family: 'JetBrains Mono', monospace;">
            <span>${prefix}</span><span id="${id}_counter" data-target="${targetVal}">0</span><span>${suffix}</span>
          </div>
        </div>`;
      }
    }

    if (type === 'shape') {
      const sc = content || {};
      const w = sc.width || 200;
      const h = sc.height || 200;
      const fill = sc.fill || '#38bdf8';
      const rad = sc.borderRadius || (sc.shapeType === 'circle' ? '50%' : '12px');
      return `<div id="${id}" class="layer" style="${style}">
        <div style="width: ${w}px; height: ${h}px; background-color: ${fill}; border-radius: ${rad};"></div>
      </div>`;
    }

    return `<div id="${id}" class="layer" style="${style}"></div>`;
  }

  private static renderSceneTimeline(scene: Scene): string {
    let script = `\n    // --- Scene Timeline: ${scene.id} (duration: ${scene.duration}s) ---\n`;
    script += `    const tl_${scene.id} = gsap.timeline({ paused: true });\n`;

    // Engine 5 Micro-Editing Directives (Punch-Ins, Gaze Centering)
    if (scene.creativeAdDirectives?.punchIn?.enabled) {
      const punchScale = scene.creativeAdDirectives.punchIn.scale || 1.25;
      const punchOrigin = scene.creativeAdDirectives.punchIn.focalTarget === 'product_center' ? '50% 50%' : '50% 35%';
      const triggerTime = scene.creativeAdDirectives.punchIn.triggerTimeSec || 0.0;
      script += `    tl_${scene.id}.to("#${scene.id}", {
        scale: ${punchScale},
        duration: 0.1,
        ease: "power2.out",
        transformOrigin: "${punchOrigin}"
      }, ${triggerTime});\n`;
    }

    for (const layer of scene.layers) {
      // Kinetic text animation
      if (layer.type === 'text' && layer.content?.kineticMode === 'word-by-word') {
        const words = (layer.content?.text || '').split(' ');
        const stagger = layer.content?.kineticStagger || 0.12;
        script += `    tl_${scene.id}.to(".kw_${layer.id}", {
          opacity: 1,
          y: 0,
          duration: 0.35,
          ease: "back.out(1.7)",
          stagger: ${stagger}
        }, ${layer.start});\n`;
      }

      // Counter ticker animation
      if (layer.type === 'chart' && layer.content?.chartType === 'counter') {
        const targetVal = layer.content?.chartData?.targetValue ?? 100;
        const startVal = layer.content?.chartData?.startValue ?? 0;
        script += `    {
          const counterObj = { val: ${startVal} };
          const counterEl = document.getElementById("${layer.id}_counter");
          tl_${scene.id}.to(counterObj, {
            val: ${targetVal},
            duration: ${Math.min(layer.duration, 2.5)},
            ease: "power2.out",
            onUpdate: function() {
              if (counterEl) counterEl.innerText = Math.floor(counterObj.val).toLocaleString();
            }
          }, ${layer.start});
        }\n`;
      }

      // Explicit animation tweens
      if (layer.animations && layer.animations.length > 0) {
        for (const anim of layer.animations) {
          const gsapEasing = GsapTweenMapper.mapEasing(anim.easing);
          const prop = GsapTweenMapper.formatProperty(anim.property);
          const fromVal = JSON.stringify(anim.from);
          const toVal = JSON.stringify(anim.to);

          script += `    tl_${scene.id}.fromTo("#${layer.id}", 
            { ${prop}: ${fromVal} }, 
            { ${prop}: ${toVal}, duration: ${anim.duration}, ease: "${gsapEasing}" }, 
            ${layer.start + anim.start});\n`;
        }
      }
    }

    script += `    window.__timelines["${scene.id}"] = tl_${scene.id};\n`;
    return script;
  }
}
