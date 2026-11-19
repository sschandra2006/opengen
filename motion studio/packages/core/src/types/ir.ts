/**
 * OpenGen Motion Graphics Studio: Intermediate Representation (IR) v1.0.0
 * Engine-agnostic declarative data structures for programmatic video production.
 */

export type AspectRatio = '16:9' | '9:16' | '1:1' | '4:5';

export type EngineType = 'hyperframes' | 'pdoom-video' | 'raea';

export type LayerType = 
  | 'text' 
  | 'image' 
  | 'video' 
  | 'vector' 
  | 'shape' 
  | 'chart' 
  | '3d-model' 
  | 'audio-reactive';

export type EasingType =
  | 'linear'
  | 'easeInQuad'
  | 'easeOutQuad'
  | 'easeInOutQuad'
  | 'easeInCubic'
  | 'easeOutCubic'
  | 'easeInOutCubic'
  | 'easeInExpo'
  | 'easeOutExpo'
  | 'easeInOutExpo'
  | 'easeInBack'
  | 'easeOutBack'
  | 'easeInOutBack'
  | 'easeInElastic'
  | 'easeOutElastic'
  | 'easeInOutElastic'
  | 'easeInBounce'
  | 'easeOutBounce'
  | 'easeInOutBounce';

export type TransitionType =
  | 'cut'
  | 'fade'
  | 'crossfade'
  | 'slide-left'
  | 'slide-right'
  | 'slide-up'
  | 'slide-down'
  | 'wipe-left'
  | 'wipe-right'
  | 'circle-open'
  | 'glitch'
  | 'zoom-in'
  | 'zoom-out';

export interface AudioSettings {
  sampleRate?: 44100 | 48000;
  channels?: 1 | 2;
  masterVolume?: number;
  targetLUFS?: number; // e.g. -14.0
  truePeak?: number;   // e.g. -1.5
}

export interface ProjectSettings {
  width: number;
  height: number;
  fps: number;
  aspectRatio: AspectRatio;
  duration: number;
  backgroundColor?: string;
  audio?: AudioSettings;
}

export interface ProjectMetadata {
  author?: string;
  createdAt?: string;
  updatedAt?: string;
  templateId?: string;
  tags?: string[];
  description?: string;
  [key: string]: any;
}

export interface AudioDuckingConfig {
  duckAgainst: 'voiceover' | 'speech' | string;
  duckVolume: number; // e.g. 0.15 (-14 dB)
  fadeDuration: number; // e.g. 0.3s
}

export interface AudioTrack {
  id: string;
  name?: string;
  type: 'music' | 'voiceover' | 'sfx' | 'ambient';
  src: string;
  start: number;
  duration: number;
  volume?: number;
  fadeIn?: number;
  fadeOut?: number;
  ducking?: AudioDuckingConfig;
}

export interface Transform {
  x?: number;
  y?: number;
  z?: number;
  scale?: number;
  scaleX?: number;
  scaleY?: number;
  rotation?: number;
  rotationX?: number;
  rotationY?: number;
  opacity?: number;
  originX?: string | number;
  originY?: string | number;
}

export interface Animation {
  property: string;
  start: number;      // Seconds relative to layer start
  duration: number;   // Duration of the tween
  from: number | string | any;
  to: number | string | any;
  easing?: EasingType | string;
}

export interface TextContent {
  text: string;
  fontSize?: number;
  fontWeight?: number | string;
  fontFamily?: string;
  color?: string;
  textAlign?: 'left' | 'center' | 'right' | 'justify';
  letterSpacing?: number;
  lineHeight?: number;
  textTransform?: 'none' | 'uppercase' | 'lowercase' | 'capitalize';
  kineticMode?: 'none' | 'word-by-word' | 'char-by-char' | 'line-by-line';
  kineticStagger?: number;
  splitDelimiters?: string[];
  maxWidth?: number;
}

export interface ImageContent {
  src: string;
  fit?: 'cover' | 'contain' | 'fill' | 'none';
  borderRadius?: number;
  border?: string;
  shadow?: string;
}

export interface VideoContent {
  src: string;
  startTime?: number;
  playbackRate?: number;
  muted?: boolean;
  loop?: boolean;
  fit?: 'cover' | 'contain';
}

export interface ChartContent {
  chartType: 'counter' | 'bar' | 'line' | 'donut' | 'progress';
  chartData: {
    targetValue?: number;
    startValue?: number;
    prefix?: string;
    suffix?: string;
    decimals?: number;
    labels?: string[];
    values?: number[];
    colors?: string[];
  };
  fontSize?: number;
  fontWeight?: number | string;
  color?: string;
  barWidth?: number;
  strokeWidth?: number;
}

export interface ThreeDContent {
  modelSrc?: string;
  meshType?: 'cube' | 'sphere' | 'plane' | 'cylinder' | 'particles' | 'custom';
  material?: {
    color?: string;
    roughness?: number;
    metalness?: number;
    wireframe?: boolean;
    emissive?: string;
  };
  lighting?: {
    ambientColor?: string;
    ambientIntensity?: number;
    directionalColor?: string;
    directionalIntensity?: number;
    directionalPosition?: [number, number, number];
  };
  camera?: {
    fov?: number;
    position?: [number, number, number];
    lookAt?: [number, number, number];
    orbitSpeed?: number;
  };
  postProcessing?: {
    bloom?: number;
    grain?: number;
    chromaticAberration?: number;
  };
}

export interface ShapeContent {
  shapeType: 'rect' | 'circle' | 'pill' | 'star' | 'polygon';
  width?: number;
  height?: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  borderRadius?: number;
}

export interface Layer {
  id: string;
  name?: string;
  type: LayerType;
  start: number;       // Start time in seconds relative to scene
  duration: number;    // Duration in seconds
  zIndex?: number;
  transform?: Transform;
  content?: TextContent | ImageContent | VideoContent | ChartContent | ThreeDContent | ShapeContent | any;
  animations?: Animation[];
  mask?: {
    type: 'rect' | 'circle' | 'path';
    invert?: boolean;
    clipPath?: string;
  };
}

export interface Transition {
  type: TransitionType;
  duration: number;
  easing?: EasingType | string;
}

export interface PunchInDirective {
  enabled: boolean;
  scale?: number;
  focalTarget?: 'face_eyes' | 'product_center' | string;
  triggerTimeSec?: number;
}

export interface SpeedRampDirective {
  leadInMultiplier?: number;
  climaxMultiplier?: number;
  revealTimeSec?: number;
}

export interface AudioPunctuationDirective {
  jCutLeadSec?: number;
  foleyCue?: 'sub_impact_heavy' | 'whoosh_slide' | 'riser_tension' | 'pop_badge' | 'camera_click' | 'notification_ding' | string;
}

export interface SafeZoneDirective {
  avoidTikTokRightSidebar?: boolean;
  bottomMarginPx?: number;
}

export interface CreativeAdDirectives {
  funnelPhase?: 'hook' | 'agitation' | 'solution_climax' | 'feature_blitz' | 'cta';
  punchIn?: PunchInDirective;
  speedRamp?: SpeedRampDirective;
  audioPunctuation?: AudioPunctuationDirective;
  safeZoneEnforcement?: SafeZoneDirective;
}

export interface Scene {
  id: string;
  name?: string;
  start: number;       // Start time in seconds relative to project
  duration: number;    // Duration in seconds
  backgroundColor?: string;
  preferredEngine?: EngineType;
  transitionIn?: Transition;
  transitionOut?: Transition;
  layers: Layer[];
  audioTracks?: AudioTrack[];
  creativeAdDirectives?: CreativeAdDirectives;
}

export interface VariableDefinition {
  type: 'string' | 'color' | 'number' | 'image' | 'audio' | 'font';
  label?: string;
  description?: string;
  default: any;
}

export interface OpenGenProject {
  schemaVersion: '1.0.0' | '1.1.0';
  projectId: string;
  title: string;
  metadata?: ProjectMetadata;
  settings: ProjectSettings;
  variables?: Record<string, VariableDefinition>;
  globalAudio?: AudioTrack[];
  scenes: Scene[];
}
