import { PunchInDirective, SpeedRampDirective } from '@opengen/core';

export class MicroEditor {
  /**
   * Generates GSAP code to apply a digital punch-in (camera scale tween) on a clip or layer.
   * Targets upper chest/facial center (50% 35%) for human speakers.
   */
  public static compilePunchInJs(targetSelector: string, directive?: PunchInDirective): string {
    if (!directive || !directive.enabled) return '';
    const scale = directive.scale || 1.25;
    const triggerTime = directive.triggerTimeSec || 0.0;
    const origin = directive.focalTarget === 'product_center' ? '50% 50%' : '50% 35%';

    return `
      // Engine 5 Micro-Edit: Dynamic Punch-In
      tl.to("${targetSelector}", {
        scale: ${scale},
        duration: 0.08,
        ease: "power2.out",
        transformOrigin: "${origin}"
      }, ${triggerTime});
    `;
  }

  /**
   * Generates GSAP / video rate manipulation for speed ramping.
   */
  public static compileSpeedRampJs(targetSelector: string, directive?: SpeedRampDirective): string {
    if (!directive) return '';
    const lead = directive.leadInMultiplier || 1.8;
    const climax = directive.climaxMultiplier || 0.65;
    const revealTime = directive.revealTimeSec || 1.5;

    return `
      // Engine 5 Micro-Edit: Speed Ramping
      const el_${Math.abs(targetSelector.hashCode?.() || 1)} = document.querySelector("${targetSelector}");
      if (el_${Math.abs(targetSelector.hashCode?.() || 1)} && el_${Math.abs(targetSelector.hashCode?.() || 1)}.tagName === 'VIDEO') {
        tl.to(el_${Math.abs(targetSelector.hashCode?.() || 1)}, {
          playbackRate: ${climax},
          duration: 0.3,
          ease: "power1.inOut"
        }, ${revealTime});
      }
    `;
  }

  /**
   * Calculates audio J-Cut offset so narration begins slightly before the visual cut.
   */
  public static calculateJCutOffset(sceneStartSec: number, leadDurationSec: number = 0.25): number {
    return Math.max(0, sceneStartSec - leadDurationSec);
  }

  /**
   * Snaps a scene or layer timestamp to the closest musical beat marker within tolerance.
   */
  public static snapToNearestBeat(
    timestamp: number,
    beatGrid: number[],
    maxToleranceSec: number = 0.12
  ): number {
    if (!beatGrid || beatGrid.length === 0) return timestamp;
    let closest = beatGrid[0];
    let minDiff = Math.abs(timestamp - closest);

    for (const b of beatGrid) {
      const diff = Math.abs(timestamp - b);
      if (diff < minDiff) {
        minDiff = diff;
        closest = b;
      }
    }

    return minDiff <= maxToleranceSec ? closest : timestamp;
  }
}
