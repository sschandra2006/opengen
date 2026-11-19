import { Animation } from '@opengen/core';

export class GsapTweenMapper {
  private static readonly EASING_MAP: Record<string, string> = {
    linear: 'none',
    easeInQuad: 'power1.in',
    easeOutQuad: 'power1.out',
    easeInOutQuad: 'power1.inOut',
    easeInCubic: 'power2.in',
    easeOutCubic: 'power2.out',
    easeInOutCubic: 'power2.inOut',
    easeInExpo: 'expo.in',
    easeOutExpo: 'expo.out',
    easeInOutExpo: 'expo.inOut',
    easeInBack: 'back.in(1.7)',
    easeOutBack: 'back.out(1.7)',
    easeInOutBack: 'back.inOut(1.7)',
    easeInElastic: 'elastic.in(1, 0.3)',
    easeOutElastic: 'elastic.out(1, 0.3)',
    easeInOutElastic: 'elastic.inOut(1, 0.3)',
    easeInBounce: 'bounce.in',
    easeOutBounce: 'bounce.out',
    easeInOutBounce: 'bounce.inOut'
  };

  public static mapEasing(easing?: string): string {
    if (!easing) return 'power2.out';
    return this.EASING_MAP[easing] || easing;
  }

  public static formatProperty(prop: string): string {
    // Normalizes properties (e.g. translate y -> y, scale -> scale)
    const normalized: Record<string, string> = {
      translateX: 'x',
      translateY: 'y',
      translateZ: 'z',
      rotate: 'rotation',
      rotateZ: 'rotation'
    };
    return normalized[prop] || prop;
  }
}
