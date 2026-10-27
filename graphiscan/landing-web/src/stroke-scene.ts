import * as THREE from 'three';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

/** Original illustrative lowercase a. This scene never analyzes handwriting. */
export function createStrokeScene(host: HTMLElement) {
  const canvas = document.createElement('canvas'); canvas.className = 'ink-canvas'; canvas.setAttribute('aria-hidden', 'true');
  const replay = document.querySelector<HTMLButtonElement>('[data-trace-replay]');
  const guidesButton = document.querySelector<HTMLButtonElement>('[data-trace-guides]');
  let renderer: THREE.WebGLRenderer;
  function fallback() {
    host.classList.remove('three-ready'); canvas.hidden = true;
    if (replay) replay.disabled = true;
    if (guidesButton) guidesButton.disabled = true;
  }
  try { renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: 'low-power' }); }
  catch { fallback(); return; }
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.6));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  host.prepend(canvas);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(37, 1, .1, 50);
  camera.position.set(0, -2.4, 6.9); camera.lookAt(0, 0, 0);
  scene.add(new THREE.AmbientLight(0xffffff, 2));
  const light = new THREE.DirectionalLight(0xffffff, 2.6); light.position.set(-3, 5, 8); scene.add(light);
  const materials: THREE.Material[] = [];
  const geometries: THREE.BufferGeometry[] = [];
  function mesh(geometry: THREE.BufferGeometry, material: THREE.Material) {
    geometries.push(geometry); materials.push(material); return new THREE.Mesh(geometry, material);
  }
  const root = new THREE.Group(); scene.add(root);
  root.rotation.z = -.08;
  const paper = mesh(new THREE.BoxGeometry(4.5, 3.3, .035), new THREE.MeshStandardMaterial({ color: '#fffdf7', roughness: .95 }));
  paper.position.set(0, 0, -.05); root.add(paper);
  const shadowCanvas = document.createElement('canvas'); shadowCanvas.width = 128; shadowCanvas.height = 128;
  const ctx = shadowCanvas.getContext('2d')!;
  const shade = ctx.createRadialGradient(64, 64, 5, 64, 64, 64); shade.addColorStop(0, 'rgba(23,42,61,.18)'); shade.addColorStop(1, 'rgba(23,42,61,0)');
  ctx.fillStyle = shade; ctx.fillRect(0, 0, 128, 128);
  const shadowTexture = new THREE.CanvasTexture(shadowCanvas);
  const shadow = mesh(new THREE.PlaneGeometry(5.8, 4.4), new THREE.MeshBasicMaterial({ map: shadowTexture, transparent: true, depthWrite: false }));
  shadow.position.set(.15, -.1, -.09); root.add(shadow);
  const guideGroup = new THREE.Group(); root.add(guideGroup); guideGroup.visible = false;
  const guideMaterial = new THREE.LineDashedMaterial({ color: '#7b9cb9', transparent: true, opacity: .55, dashSize: .07, gapSize: .05 }); materials.push(guideMaterial);
  for (const y of [-.62, .15, .88]) {
    const geometry = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-2.1, y, -.025), new THREE.Vector3(2.1, y, -.025)]); geometries.push(geometry);
    const line = new THREE.Line(geometry, guideMaterial); line.computeLineDistances(); guideGroup.add(line);
  }
  const curve = new THREE.CurvePath<THREE.Vector3>();
  const v = (x: number, y: number) => new THREE.Vector3(x, y, .005);
  curve.add(new THREE.CubicBezierCurve3(v(.5, .72), v(-.9, 1.12), v(-1.05, -.73), v(-.12, -.65)));
  curve.add(new THREE.CubicBezierCurve3(v(-.12, -.65), v(.62, -.6), v(.74, .28), v(.5, .72)));
  curve.add(new THREE.CubicBezierCurve3(v(.5, .72), v(.48, .21), v(.3, -.75), v(.55, -.68)));
  curve.add(new THREE.CubicBezierCurve3(v(.55, -.68), v(.72, -.7), v(.86, -.6), v(.99, -.5)));
  const inkGeometry = new THREE.TubeGeometry(curve, 240, .028, 8, false); geometries.push(inkGeometry);
  const inkMaterial = new THREE.MeshStandardMaterial({ color: '#355c8c', roughness: .35, metalness: .06 }); materials.push(inkMaterial);
  const ink = new THREE.Mesh(inkGeometry, inkMaterial); root.add(ink);
  const indexCount = inkGeometry.index!.count;
  const pen = new THREE.Group(); root.add(pen);
  const barrel = mesh(new THREE.CylinderGeometry(.065, .065, 1.35, 18), new THREE.MeshStandardMaterial({ color: '#263d56', metalness: .3, roughness: .25 }));
  barrel.rotation.x = Math.PI / 2; barrel.position.z = .95; pen.add(barrel);
  const tip = mesh(new THREE.ConeGeometry(.06, .34, 14), new THREE.MeshStandardMaterial({ color: '#a0a8b1', metalness: .8, roughness: .25 }));
  tip.rotation.x = -Math.PI / 2; tip.position.z = .17; pen.add(tip);
  const ring = mesh(new THREE.CylinderGeometry(.068, .068, .05, 18), new THREE.MeshStandardMaterial({ color: '#aab3bd', metalness: .8, roughness: .2 }));
  ring.rotation.x = Math.PI / 2; ring.position.z = .37; pen.add(ring);
  pen.rotation.set(-.45, .2, 0);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const state = { progress: 0, lift: 0 };
  let visible = true, disposed = false, contextLost = false;
  let animation: gsap.core.Timeline | undefined;
  function render() {
    if (!visible || disposed || contextLost || document.hidden) return;
    inkGeometry.setDrawRange(0, Math.floor(indexCount * state.progress / 6) * 6);
    const point = curve.getPointAt(Math.max(0, Math.min(1, state.progress)));
    pen.position.copy(point); pen.position.z += state.lift;
    pen.visible = !reduced.matches && state.lift < .48;
    renderer.render(scene, camera);
    canvas.dataset.progress = state.progress.toFixed(3);
    canvas.dataset.guides = String(guideGroup.visible);
  }
  function resize() {
    const { width, height } = host.getBoundingClientRect(); renderer.setSize(width, height, false);
    camera.aspect = width / height; camera.position.z = width < 400 ? 8.7 : 6.9; camera.updateProjectionMatrix(); render();
  }
  function trace() {
    animation?.kill();
    if (reduced.matches) { state.progress = 1; state.lift = .5; render(); return; }
    state.progress = 0; state.lift = 0;
    animation = gsap.timeline({ onUpdate: render }).to(state, { progress: 1, duration: 2.8, ease: 'none' }).to(state, { lift: .5, duration: .5, ease: 'power2.out' });
  }
  function toggleGuides() { guideGroup.visible = !guideGroup.visible; guidesButton?.setAttribute('aria-pressed', String(guideGroup.visible)); if (guidesButton) guidesButton.textContent = guideGroup.visible ? 'Hide guides' : 'Show guides'; render(); }
  replay?.addEventListener('click', trace); guidesButton?.addEventListener('click', toggleGuides);
  reduced.addEventListener('change', trace);
  const resizeObserver = new ResizeObserver(resize); resizeObserver.observe(host);
  const visibilityObserver = new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting;
    if (!visible) animation?.pause(); else { animation?.resume(); render(); }
  }); visibilityObserver.observe(host);
  const onVisibility = () => { if (document.hidden) animation?.pause(); else if (visible) { animation?.resume(); render(); } };
  document.addEventListener('visibilitychange', onVisibility);
  canvas.addEventListener('webglcontextlost', event => { event.preventDefault(); contextLost = true; animation?.kill(); fallback(); });
  resize(); render(); host.classList.add('three-ready');
  if (replay) replay.disabled = false;
  if (guidesButton) guidesButton.disabled = false;
  const entrance = ScrollTrigger.create({ trigger: host, start: 'top 90%', onEnter: trace, once: true });
  if (reduced.matches) trace();
  function dispose() {
    disposed = true; animation?.kill(); entrance.kill();
    resizeObserver.disconnect(); visibilityObserver.disconnect(); reduced.removeEventListener('change', trace);
    replay?.removeEventListener('click', trace); guidesButton?.removeEventListener('click', toggleGuides); document.removeEventListener('visibilitychange', onVisibility);
    geometries.forEach(geometry => geometry.dispose()); [...new Set(materials)].forEach(material => material.dispose()); shadowTexture.dispose(); renderer.dispose();
  }
  addEventListener('pagehide', event => { if (!(event as PageTransitionEvent).persisted) dispose(); }, { once: true });
  if (import.meta.hot) import.meta.hot.dispose(dispose);
}
