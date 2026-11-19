export interface AudioTelemetry {
  duration: number;
  tempo: number;
  beats: number[];
  downbeats: number[];
  events: Array<{ type: string; time: number }>;
}

export interface FrameContext {
  t: number;      // Current timestamp in seconds
  frame: number;  // Current frame index
  fps: number;    // Frames per second
  audio?: AudioTelemetry;
}

export abstract class SceneBase {
  public duration: number;
  public width: number;
  public height: number;

  constructor(width: number, height: number, duration: number) {
    this.width = width;
    this.height = height;
    this.duration = duration;
  }

  public abstract init(): Promise<void>;
  
  /**
   * Deterministic frame update based purely on time t and frame index
   */
  public abstract update(ctx: FrameContext): void;
}
