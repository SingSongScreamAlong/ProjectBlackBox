import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass';

export interface TrackCoordinate {
  x: number;
  y: number;
  z: number;
  sectorIndex?: number;
}

export interface DriverPosition {
  driverId: string;
  driverName: string;
  position: number;
  x: number;
  y: number;
  z: number;
  speed: number;
  teamColor: string;
}

export interface CameraMode {
  type: 'follow' | 'orbit' | 'broadcast' | 'helicopter' | 'onboard';
  targetDriverId?: string;
}

export class Track3DRenderer {
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private composer!: EffectComposer;

  private trackMesh: THREE.Mesh | null = null;
  private trackLine: THREE.Line | null = null;
  private driverMeshes: Map<string, THREE.Mesh> = new Map();
  private driverTrails: Map<string, THREE.Line> = new Map();
  private sectorMarkers: THREE.Group = new THREE.Group();

  private animationFrameId: number | null = null;
  private cameraMode: CameraMode = { type: 'orbit' };

  private trackWidth: number = 12; // Track width in meters
  private trackColor: number = 0x2a2a2a; // Dark asphalt
  private trackBoundaryColor: number = 0xff0000; // Red/white curbs

  constructor(private container: HTMLElement) {
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(
      60,
      container.clientWidth / container.clientHeight,
      0.1,
      10000
    );

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true
    });
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;

    container.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.maxPolarAngle = Math.PI / 2.2;
    this.controls.minDistance = 50;
    this.controls.maxDistance = 2000;

    this.setupPostProcessing();
    this.setupLighting();
    this.setupEnvironment();

    window.addEventListener('resize', this.handleResize.bind(this));
  }

  private setupPostProcessing(): void {
    this.composer = new EffectComposer(this.renderer);

    const renderPass = new RenderPass(this.scene, this.camera);
    this.composer.addPass(renderPass);

    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
      0.5,  // strength
      0.4,  // radius
      0.85  // threshold
    );
    this.composer.addPass(bloomPass);
  }

  private setupLighting(): void {
    // Ambient light for overall illumination
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambientLight);

    // Main directional light (sun)
    const sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
    sunLight.position.set(100, 200, 100);
    sunLight.castShadow = true;
    sunLight.shadow.camera.left = -500;
    sunLight.shadow.camera.right = 500;
    sunLight.shadow.camera.top = 500;
    sunLight.shadow.camera.bottom = -500;
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 1000;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    this.scene.add(sunLight);

    // Hemisphere light for realistic sky/ground lighting
    const hemiLight = new THREE.HemisphereLight(0x87CEEB, 0x6B8E23, 0.4);
    this.scene.add(hemiLight);
  }

  private setupEnvironment(): void {
    // Sky gradient background
    const skyColor = new THREE.Color(0x87CEEB);
    const groundColor = new THREE.Color(0x6B8E23);
    this.scene.background = skyColor;

    // Ground plane
    const groundGeometry = new THREE.PlaneGeometry(5000, 5000);
    const groundMaterial = new THREE.MeshStandardMaterial({
      color: 0x3a6e2b,
      roughness: 0.9,
      metalness: 0.1,
    });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.5;
    ground.receiveShadow = true;
    this.scene.add(ground);

    // Grid for reference (optional, can be toggled)
    const gridHelper = new THREE.GridHelper(2000, 100, 0x444444, 0x222222);
    gridHelper.position.y = -0.4;
    this.scene.add(gridHelper);
  }

  /**
   * Create track from telemetry coordinates
   * Works for any track type: oval, road course, street circuit, etc.
   */
  public createTrack(coordinates: TrackCoordinate[]): void {
    if (coordinates.length < 3) {
      console.error('Need at least 3 coordinates to create track');
      return;
    }

    // Clear existing track
    if (this.trackMesh) {
      this.scene.remove(this.trackMesh);
      this.trackMesh = null;
    }
    if (this.trackLine) {
      this.scene.remove(this.trackLine);
      this.trackLine = null;
    }

    // Create track path
    const trackPoints = coordinates.map(
      coord => new THREE.Vector3(coord.x, coord.y, coord.z)
    );

    // Close the loop
    trackPoints.push(trackPoints[0].clone());

    const trackCurve = new THREE.CatmullRomCurve3(trackPoints, true);
    const trackGeometry = new THREE.TubeGeometry(
      trackCurve,
      coordinates.length * 2, // segments
      this.trackWidth / 2,     // radius (half width)
      8,                       // radial segments
      false                    // closed
    );

    const trackMaterial = new THREE.MeshStandardMaterial({
      color: this.trackColor,
      roughness: 0.85,
      metalness: 0.15,
      side: THREE.DoubleSide,
    });

    this.trackMesh = new THREE.Mesh(trackGeometry, trackMaterial);
    this.trackMesh.castShadow = true;
    this.trackMesh.receiveShadow = true;
    this.scene.add(this.trackMesh);

    // Create track centerline for reference
    const lineGeometry = new THREE.BufferGeometry().setFromPoints(trackPoints);
    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0xffff00,
      linewidth: 2,
      transparent: true,
      opacity: 0.3,
    });
    this.trackLine = new THREE.Line(lineGeometry, lineMaterial);
    this.trackLine.position.y = 0.1; // Slightly above track
    this.scene.add(this.trackLine);

    // Add curbs/track boundaries
    this.createTrackBoundaries(trackCurve, coordinates.length * 2);

    // Create sector markers if provided
    this.createSectorMarkers(coordinates);

    // Center camera on track
    this.centerCameraOnTrack(trackPoints);
  }

  private createTrackBoundaries(curve: THREE.CatmullRomCurve3, segments: number): void {
    const boundaryOffset = this.trackWidth / 2 + 0.5;

    // Inner boundary (red/white curbs)
    const innerPoints = [];
    const outerPoints = [];

    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const point = curve.getPointAt(t);
      const tangent = curve.getTangentAt(t);

      const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();

      const innerPoint = point.clone().add(normal.multiplyScalar(-boundaryOffset));
      const outerPoint = point.clone().add(normal.multiplyScalar(boundaryOffset));

      innerPoints.push(innerPoint);
      outerPoints.push(outerPoint);
    }

    // Create curb geometry (alternating red/white)
    [innerPoints, outerPoints].forEach((points, idx) => {
      const curbGeometry = new THREE.BufferGeometry().setFromPoints(points);
      const curbMaterial = new THREE.LineBasicMaterial({
        color: idx === 0 ? 0xff0000 : 0xffffff,
        linewidth: 3,
      });
      const curb = new THREE.Line(curbGeometry, curbMaterial);
      curb.position.y = 0.05;
      this.scene.add(curb);
    });
  }

  private createSectorMarkers(coordinates: TrackCoordinate[]): void {
    this.scene.remove(this.sectorMarkers);
    this.sectorMarkers = new THREE.Group();

    const sectors = new Map<number, TrackCoordinate>();
    coordinates.forEach(coord => {
      if (coord.sectorIndex !== undefined && !sectors.has(coord.sectorIndex)) {
        sectors.set(coord.sectorIndex, coord);
      }
    });

    sectors.forEach((coord, sectorIndex) => {
      const markerGeometry = new THREE.CylinderGeometry(2, 2, 10, 8);
      const markerMaterial = new THREE.MeshStandardMaterial({
        color: sectorIndex === 0 ? 0x00ff00 : sectorIndex === 1 ? 0xffff00 : 0xff00ff,
        emissive: sectorIndex === 0 ? 0x00ff00 : sectorIndex === 1 ? 0xffff00 : 0xff00ff,
        emissiveIntensity: 0.5,
      });

      const marker = new THREE.Mesh(markerGeometry, markerMaterial);
      marker.position.set(coord.x, coord.y + 5, coord.z);
      this.sectorMarkers.add(marker);
    });

    this.scene.add(this.sectorMarkers);
  }

  private centerCameraOnTrack(trackPoints: THREE.Vector3[]): void {
    const box = new THREE.Box3().setFromPoints(trackPoints);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());

    const maxDim = Math.max(size.x, size.y, size.z);
    const fov = this.camera.fov * (Math.PI / 180);
    const cameraDistance = Math.abs(maxDim / Math.tan(fov / 2)) * 1.5;

    this.camera.position.set(
      center.x + cameraDistance * 0.5,
      center.y + cameraDistance * 0.8,
      center.z + cameraDistance * 0.5
    );
    this.camera.lookAt(center);
    this.controls.target.copy(center);
    this.controls.update();
  }

  /**
   * Update driver positions in real-time
   * Universal for all racing types (oval, road, etc.)
   */
  public updateDrivers(drivers: DriverPosition[]): void {
    const currentDriverIds = new Set(drivers.map(d => d.driverId));

    // Remove drivers that are no longer present
    this.driverMeshes.forEach((mesh, driverId) => {
      if (!currentDriverIds.has(driverId)) {
        this.scene.remove(mesh);
        this.driverMeshes.delete(driverId);

        const trail = this.driverTrails.get(driverId);
        if (trail) {
          this.scene.remove(trail);
          this.driverTrails.delete(driverId);
        }
      }
    });

    // Update or create driver cars
    drivers.forEach(driver => {
      let carMesh = this.driverMeshes.get(driver.driverId);

      if (!carMesh) {
        // Create new car mesh
        carMesh = this.createCarMesh(driver.teamColor);
        this.driverMeshes.set(driver.driverId, carMesh);
        this.scene.add(carMesh);

        // Create motion trail
        const trailGeometry = new THREE.BufferGeometry();
        const trailMaterial = new THREE.LineBasicMaterial({
          color: driver.teamColor,
          transparent: true,
          opacity: 0.6,
          linewidth: 2,
        });
        const trail = new THREE.Line(trailGeometry, trailMaterial);
        this.driverTrails.set(driver.driverId, trail);
        this.scene.add(trail);
      }

      // Update car position
      carMesh.position.set(driver.x, driver.y, driver.z);

      // Update trail
      this.updateDriverTrail(driver.driverId, driver.x, driver.y, driver.z);
    });

    // Update camera based on mode
    this.updateCamera(drivers);
  }

  private createCarMesh(color: string): THREE.Mesh {
    // Simple car geometry (can be replaced with GLB models)
    const carGroup = new THREE.Group();

    // Car body
    const bodyGeometry = new THREE.BoxGeometry(2, 0.8, 4);
    const bodyMaterial = new THREE.MeshStandardMaterial({
      color: color,
      metalness: 0.7,
      roughness: 0.3,
    });
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
    body.castShadow = true;
    carGroup.add(body);

    // Cockpit
    const cockpitGeometry = new THREE.BoxGeometry(1.5, 0.6, 2);
    const cockpitMaterial = new THREE.MeshStandardMaterial({
      color: 0x111111,
      metalness: 0.9,
      roughness: 0.1,
      transparent: true,
      opacity: 0.8,
    });
    const cockpit = new THREE.Mesh(cockpitGeometry, cockpitMaterial);
    cockpit.position.y = 0.7;
    cockpit.castShadow = true;
    carGroup.add(cockpit);

    // Wheels
    const wheelGeometry = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
    const wheelMaterial = new THREE.MeshStandardMaterial({
      color: 0x222222,
      roughness: 0.9,
    });

    const wheelPositions = [
      [-1, -0.3, 1.5],  // Front left
      [1, -0.3, 1.5],   // Front right
      [-1, -0.3, -1.5], // Rear left
      [1, -0.3, -1.5],  // Rear right
    ];

    wheelPositions.forEach(pos => {
      const wheel = new THREE.Mesh(wheelGeometry, wheelMaterial);
      wheel.rotation.z = Math.PI / 2;
      wheel.position.set(pos[0], pos[1], pos[2]);
      wheel.castShadow = true;
      carGroup.add(wheel);
    });

    // Position indicator light on top
    const lightGeometry = new THREE.SphereGeometry(0.3, 8, 8);
    const lightMaterial = new THREE.MeshStandardMaterial({
      color: color,
      emissive: color,
      emissiveIntensity: 2,
    });
    const light = new THREE.Mesh(lightGeometry, lightMaterial);
    light.position.y = 1.5;
    carGroup.add(light);

    return carGroup as unknown as THREE.Mesh;
  }

  private updateDriverTrail(driverId: string, x: number, y: number, z: number): void {
    const trail = this.driverTrails.get(driverId);
    if (!trail) return;

    const positions = trail.geometry.attributes.position;
    const maxTrailPoints = 50;

    const currentPoints: number[] = positions ? Array.from(positions.array as Float32Array) : [];

    // Add new point
    currentPoints.push(x, y + 0.5, z);

    // Limit trail length
    if (currentPoints.length > maxTrailPoints * 3) {
      currentPoints.splice(0, 3);
    }

    // Update geometry
    const newPositions = new Float32Array(currentPoints);
    trail.geometry.setAttribute('position', new THREE.BufferAttribute(newPositions, 3));
    trail.geometry.attributes.position.needsUpdate = true;
  }

  private updateCamera(drivers: DriverPosition[]): void {
    if (this.cameraMode.type === 'follow' && this.cameraMode.targetDriverId) {
      const targetDriver = drivers.find(d => d.driverId === this.cameraMode.targetDriverId);
      if (targetDriver) {
        const targetPos = new THREE.Vector3(targetDriver.x, targetDriver.y, targetDriver.z);
        const offset = new THREE.Vector3(0, 20, -30);
        this.camera.position.lerp(targetPos.clone().add(offset), 0.1);
        this.camera.lookAt(targetPos);
      }
    } else if (this.cameraMode.type === 'broadcast') {
      // Broadcast camera: sweep across track
      const time = Date.now() * 0.0001;
      this.camera.position.x = Math.cos(time) * 200;
      this.camera.position.z = Math.sin(time) * 200;
      this.camera.position.y = 100;
      this.camera.lookAt(0, 0, 0);
    }
  }

  public setCameraMode(mode: CameraMode): void {
    this.cameraMode = mode;

    if (mode.type === 'orbit') {
      this.controls.enabled = true;
    } else {
      this.controls.enabled = false;
    }
  }

  public animate(): void {
    this.animationFrameId = requestAnimationFrame(this.animate.bind(this));

    if (this.controls.enabled) {
      this.controls.update();
    }

    this.composer.render();
  }

  public startAnimation(): void {
    if (!this.animationFrameId) {
      this.animate();
    }
  }

  public stopAnimation(): void {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  private handleResize(): void {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;

    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();

    this.renderer.setSize(width, height);
    this.composer.setSize(width, height);
  }

  public dispose(): void {
    this.stopAnimation();

    window.removeEventListener('resize', this.handleResize.bind(this));

    this.scene.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        object.geometry.dispose();
        if (Array.isArray(object.material)) {
          object.material.forEach(material => material.dispose());
        } else {
          object.material.dispose();
        }
      }
    });

    this.renderer.dispose();
    this.container.removeChild(this.renderer.domElement);
  }
}
