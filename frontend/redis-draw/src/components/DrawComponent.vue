<template>
  <div>
    <div class="q-ma-xs">
      <canvas
        id="hcanvas"
        width="2000"
        height="2000"
        style="visibility: hidden; display: none"
      ></canvas>
      <canvas
        id="canvas"
        class="canvas"
        style="cursor: crosshair; border: 1px solid"
      ></canvas>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { api } from '../boot/axios';
import { CanvasCommand, UUIDResponse } from './models';
import { useDrawStore } from '../stores/draw';
import { useToolbarStore } from '../stores/toolbar';
import { useMetricsStore } from '../stores/metrics';

const contextmenu = ref(false);
const contextc = ref({
  x: 0,
  y: 0,
});

function setContextMenu(value: boolean) {
  contextmenu.value = value;
  if (contextmenu.value) {
    const { realX, realY } = getRealCoordinates(event);
    contextc.value.x = realX;
    contextc.value.y = realY;
  }
  canvas.style.cursor = contextmenu.value ? 'grab' : 'crosshair';
}

const canvasOffset = ref({
  x: 0,
  y: 0,
});
function isValidUUID(str: string): boolean {
  const regexExp =
    /^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$/gi;
  return regexExp.test(str);
}

const metrics = useMetricsStore();

const drawstore = useDrawStore();
const toolbarstore = useToolbarStore();

const canvas_uuid = ref('');

let canvas: HTMLCanvasElement;
let hcanvas: HTMLCanvasElement;
let canvasCtx: CanvasRenderingContext2D;
let hcanvasCtx: CanvasRenderingContext2D;
let ws: WebSocket;

async function getCanvasUUID(): Promise<void> {
  let uuid = window.location.hash.substr(1);
  if (!isValidUUID(uuid)) {
    const response = await api.get('/api/uuid/new');
    const data: UUIDResponse = (await response.data) as UUIDResponse;
    window.location.hash = `#${data.uuid}`;
    uuid = data.uuid;
    canvas_uuid.value = uuid;
    startWebSocket(data.uuid);
  } else {
    startWebSocket(uuid);
  }
}

onMounted(() => {
  canvas = document.getElementById('canvas') as HTMLCanvasElement;
  canvasCtx = canvas.getContext('2d') as CanvasRenderingContext2D;
  hcanvas = document.getElementById('hcanvas') as HTMLCanvasElement;
  hcanvasCtx = hcanvas.getContext('2d') as CanvasRenderingContext2D;
  canvas.height = Math.min(window.innerHeight * 0.9, 2000);
  canvas.width = Math.min(window.innerWidth * 0.95, 2000);
  canvas.addEventListener('contextmenu', (event) => event.preventDefault());
  canvas.addEventListener('mousemove', (event) => mouseMoveOrTouchMove(event));
  canvas.addEventListener('touchmove', (event) => mouseMoveOrTouchMove(event));
  canvas.addEventListener('mousedown', (event) => mouseDownOrTouchStart(event));
  canvas.addEventListener('touchstart', (event) =>
    mouseDownOrTouchStart(event)
  );
  canvas.addEventListener('touchend', () => {
    setContextMenu(false);
  });
  canvas.addEventListener('mouseout', function (event) {
    event.preventDefault();
    localX = -1;
    localY = -1;
    metrics.setCoordinates(0, 0);
    setContextMenu(false);
  });
  canvas.addEventListener('mouseup', () => setContextMenu(false));
  void getCanvasUUID();
  draw();

  window.addEventListener('resize', () => {
    drawBuf.push({
      t: 'movecanvas',
    });
  });
});

function startWebSocket(uuid: string) {
  if (location.protocol !== 'https:') {
    ws = new WebSocket(`ws://${window.location.host}/ws/${uuid}`);
  } else {
    ws = new WebSocket(`wss://${window.location.host}/ws/${uuid}`);
  }

  ws.onopen = function () {
    void api.get(`api/sub/${uuid}`);
    clearAllCanvases();
    ws.send(
      JSON.stringify({
        t: 'connected',
      })
    );
  };

  ws.onmessage = (event: MessageEvent) => {
    const data = JSON.parse(<string>event.data) as CanvasCommand;
    const d = new Date();
    data.cdelay = d.getTime() - data.ctime;
    metrics.setReceivedMetrics(data.sdelay, data.cdelay);

    if (data.error) {
      console.log(data);
    } else {
      drawBuf.push(data);
    }
  };
  ws.onclose = function () {
    setTimeout(() => {
      startWebSocket(uuid);
    }, 2000);
  };
}

function wsSendObject(obj: CanvasCommand): void {
  //console.log(obj);
  const d = new Date();
  obj.ctime = d.getTime();
  ws.send(JSON.stringify(obj));
  metrics.setSentMetrics();
  //console.log(metrics);
}

function sendLineDrawCoords(fx: number, fy: number, tx: number, ty: number) {
  wsSendObject({
    fx: fx,
    fy: fy,
    tx: tx,
    ty: ty,
    color: drawstore.brushcolor,
    width: drawstore.brushwidth,
    t: 'line',
  } as CanvasCommand);
}
function sendPointDrawCoords(x: number, y: number): void {
  wsSendObject({
    x: x,
    y: y,
    color: drawstore.brushcolor,
    width: drawstore.brushwidth,
    t: 'point',
  } as CanvasCommand);
}

/*
function sendCanvasClear(): void {
    wsSendObject({
        t: 'clear'
    } as CanvasCommand)
}
*/

let localX = 0;
let localY = 0;

function getRealCoordinates(event: MouseEvent | TouchEvent) {
  toolbarstore.visible = false;
  let y: number;
  let x: number;
  const touches = event.touches as TouchList;
  if (touches) {
    x = touches[0].clientX;
    y = touches[0].clientY;
  } else {
    x = <number>event.clientX;
    y = <number>event.clientY;
  }
  const rect = canvas.getBoundingClientRect();
  const realX = x - rect.left + canvasOffset.value.x;
  const realY = y - rect.top + canvasOffset.value.y;
  metrics.setCoordinates(realX, realY);

  return { realX, realY };
}

function mouseDownOrTouchStart(event: MouseEvent | TouchEvent) {
  const { realX, realY } = getRealCoordinates(event);

  let numtouch = 0;
  if (event.touches) {
    numtouch = event.touches.length;
    if (numtouch > 1) {
      setContextMenu(true);
      return;
    }
  } else if (event.buttons === 2) {
    setContextMenu(true);
    return;
  }

  if (event.buttons !== 1 && numtouch !== 1) return;

  if (localX === -1 && localY === -1) {
    localX = realX;
    localY = realY;
  }
  if (localX !== realX || localY !== realY) {
    sendPointDrawCoords(realX, realY);
    localX = realX;
    localY = realY;
  }
  sendPointDrawCoords(realX, realY);
}

function mouseMoveOrTouchMove(event: MouseEvent | TouchEvent) {
  if (event.touches) {
    event.preventDefault();
  }
  const { realX, realY } = getRealCoordinates(event);

  // hack to clear all text selections as they screw up things
  if (window.getSelection) {
    window.getSelection().removeAllRanges();
  }
  if (event.buttons !== 1 && !event.touches && !contextmenu.value) return;

  if (localX === -1 && localY === -1) {
    localX = realX;
    localY = realY;
  }
  if (localX !== realX || localY !== realY) {
    if (contextmenu.value) {
      changeOffset(contextc.value.x - realX, contextc.value.y - realY);
    } else {
      sendLineDrawCoords(localX, localY, realX, realY);
    }
    localX = realX;
    localY = realY;
  }
}

function changeOffset(x: number, y: number) {
  const offsetX = canvasOffset.value.x + x;
  if (offsetX >= 0 && canvas.width + offsetX <= hcanvas.width) {
    canvasOffset.value.x = offsetX;
  } else if (canvas.width + offsetX > hcanvas.width) {
    canvasOffset.value.x = hcanvas.width - canvas.width;
  } else {
    canvasOffset.value.x = 0;
  }
  const offsetY = canvasOffset.value.y + y;
  if (offsetY >= 0 && canvas.height + offsetY <= hcanvas.height) {
    canvasOffset.value.y = offsetY;
  } else if (canvas.height + offsetY > hcanvas.height) {
    canvasOffset.value.y = hcanvas.height - canvas.height;
  } else {
    canvasOffset.value.y = 0;
  }
  //alert(canvasOffset.value.x);
  const task = {
    t: 'movecanvas',
  };
  drawBuf.push(task);
}

let drawBuf = [];
function draw() {
  for (const [i, task] of drawBuf.entries()) {
    if (task.t === 'movecanvas') {
      canvas.height = Math.min(window.innerHeight * 0.9, 2000);
      canvas.width = Math.min(window.innerWidth * 0.95, 2000);
      const imageData = hcanvasCtx.getImageData(
        canvasOffset.value.x,
        canvasOffset.value.y,
        canvas.width,
        canvas.height
      );
      canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
      canvasCtx.putImageData(imageData, 0, 0);
    } else if (task.t === 'line') {
      drawCanvasLine(
        task.fx,
        task.fy,
        task.tx,
        task.ty,
        task.color,
        task.width
      );
    } else if (task.t === 'point') {
      drawPointToCanvas(task.x, task.y, task.color, task.width);
    }
    drawBuf.splice(i, 1);
  }
  requestAnimationFrame(draw);
}

function drawCanvasLine(
  fx: number,
  fy: number,
  tx: number,
  ty: number,
  color: string,
  width: number
) {
  for (const ctx of [canvasCtx, hcanvasCtx]) {
    let xoffset = 0;
    let yoffset = 0;
    if (ctx === canvasCtx) {
      xoffset = canvasOffset.value.x;
      yoffset = canvasOffset.value.y;
    }
    ctx.beginPath();
    ctx.lineWidth = width;
    ctx.lineCap = 'round';
    ctx.moveTo(fx - xoffset, fy - yoffset);
    ctx.lineTo(tx - xoffset, ty - yoffset);
    ctx.strokeStyle = color;
    ctx.stroke();
  }
}

function drawPointToCanvas(x: number, y: number, color: string, width: number) {
  let xoffset = 0;
  let yoffset = 0;
  for (const ctx of [canvasCtx, hcanvasCtx]) {
    if (ctx === canvasCtx) {
      xoffset = canvasOffset.value.x;
      yoffset = canvasOffset.value.y;
    }
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 1;
    ctx.arc(x - xoffset, y - yoffset, width / 2, 0, 2 * Math.PI);
    ctx.fill();
  }
}

function clearAllCanvases() {
  for (const ctx of [canvasCtx, hcanvasCtx]) {
    if (ctx === canvasCtx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    } else {
      ctx.clearRect(0, 0, hcanvas.width, hcanvas.height);
    }
  }
}
</script>
