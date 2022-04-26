export interface CanvasCommand {
  t?: string;
  c?: string;
  m?: string;
  ctime?: number;
  cdelay?: number;
  stime?: number;
  sdelay?: number;
  fx?: number;
  fy?: number;
  tx?: number;
  ty?: number;
  x?: number;
  y?: number;
  color?: string;
  width?: number;
  error: string;
}

export interface UUIDResponse {
  uuid: string;
}

export interface CanvasElement {
  name: string;
  canvas: HTMLCanvasElement;
  ctx: CanvasRenderingContext2D;
  source?: string;
}
