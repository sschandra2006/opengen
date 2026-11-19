import {
  OpenGenProject,
  ProjectSettings,
  ProjectMetadata,
  Scene,
  Layer,
  Animation,
  AudioTrack,
  Transform,
  Transition,
  LayerType,
  EngineType,
  EasingType
} from '../types/ir';

export class LayerBuilder {
  private layer: Layer;

  constructor(id: string, type: LayerType, duration: number) {
    this.layer = {
      id,
      type,
      start: 0,
      duration,
      zIndex: 1,
      transform: {},
      animations: []
    };
  }

  public static create(id: string, type: LayerType, duration: number): LayerBuilder {
    return new LayerBuilder(id, type, duration);
  }

  public setStart(start: number): this {
    this.layer.start = start;
    return this;
  }

  public setZIndex(zIndex: number): this {
    this.layer.zIndex = zIndex;
    return this;
  }

  public setTransform(transform: Transform): this {
    this.layer.transform = { ...this.layer.transform, ...transform };
    return this;
  }

  public setContent(content: any): this {
    this.layer.content = content;
    return this;
  }

  public addAnimation(animation: Animation): this {
    this.layer.animations = this.layer.animations || [];
    this.layer.animations.push(animation);
    return this;
  }

  public animate(
    property: string,
    start: number,
    duration: number,
    from: any,
    to: any,
    easing: EasingType | string = 'easeOutCubic'
  ): this {
    return this.addAnimation({ property, start, duration, from, to, easing });
  }

  public build(): Layer {
    return this.layer;
  }
}

export class SceneBuilder {
  private scene: Scene;

  constructor(id: string, duration: number) {
    this.scene = {
      id,
      name: id,
      start: 0,
      duration,
      layers: [],
      audioTracks: []
    };
  }

  public static create(id: string, duration: number): SceneBuilder {
    return new SceneBuilder(id, duration);
  }

  public setName(name: string): this {
    this.scene.name = name;
    return this;
  }

  public setStart(start: number): this {
    this.scene.start = start;
    return this;
  }

  public setBackgroundColor(color: string): this {
    this.scene.backgroundColor = color;
    return this;
  }

  public setPreferredEngine(engine: EngineType): this {
    this.scene.preferredEngine = engine;
    return this;
  }

  public setTransitionOut(transition: Transition): this {
    this.scene.transitionOut = transition;
    return this;
  }

  public addLayer(layer: Layer | LayerBuilder): this {
    const l = layer instanceof LayerBuilder ? layer.build() : layer;
    this.scene.layers.push(l);
    return this;
  }

  public addAudioTrack(track: AudioTrack): this {
    this.scene.audioTracks = this.scene.audioTracks || [];
    this.scene.audioTracks.push(track);
    return this;
  }

  public build(): Scene {
    return this.scene;
  }
}

export class ProjectBuilder {
  private project: OpenGenProject;

  constructor(projectId: string, settings: Partial<ProjectSettings> = {}) {
    this.project = {
      schemaVersion: '1.0.0',
      projectId,
      title: projectId,
      settings: {
        width: settings.width || 1080,
        height: settings.height || 1920,
        fps: settings.fps || 30,
        aspectRatio: settings.aspectRatio || '9:16',
        duration: settings.duration || 15.0,
        backgroundColor: settings.backgroundColor || '#0a0e17',
        audio: {
          sampleRate: 48000,
          channels: 2,
          masterVolume: 1.0,
          targetLUFS: -14.0,
          truePeak: -1.5,
          ...(settings.audio || {})
        }
      },
      globalAudio: [],
      scenes: []
    };
  }

  public static create(projectId: string, settings?: Partial<ProjectSettings>): ProjectBuilder {
    return new ProjectBuilder(projectId, settings);
  }

  public setTitle(title: string): this {
    this.project.title = title;
    return this;
  }

  public setMetadata(metadata: ProjectMetadata): this {
    this.project.metadata = metadata;
    return this;
  }

  public setDuration(duration: number): this {
    this.project.settings.duration = duration;
    return this;
  }

  public setBackgroundColor(color: string): this {
    this.project.settings.backgroundColor = color;
    return this;
  }

  public addGlobalAudio(track: AudioTrack): this {
    this.project.globalAudio = this.project.globalAudio || [];
    this.project.globalAudio.push(track);
    return this;
  }

  public addScene(scene: Scene | SceneBuilder): this {
    const s = scene instanceof SceneBuilder ? scene.build() : scene;
    this.project.scenes.push(s);
    return this;
  }

  public build(): OpenGenProject {
    // Recompute scene start times if unset
    let currentStart = 0;
    this.project.scenes.forEach(s => {
      if (s.start === undefined || s.start === 0 && currentStart > 0) {
        s.start = currentStart;
      }
      currentStart = s.start + s.duration;
    });

    if (this.project.settings.duration <= 0 && currentStart > 0) {
      this.project.settings.duration = currentStart;
    }

    return this.project;
  }
}
