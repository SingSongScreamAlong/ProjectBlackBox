import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass';

export interface Track3DConfig {
    container: HTMLElement;
    width: number;
    height: number;
    isDarkTheme?: boolean;
}

export class Track3DRenderer {
    private scene: THREE.Scene;
    private camera: THREE.PerspectiveCamera;
    private renderer: THREE.WebGLRenderer;
    private controls: OrbitControls;
    private composer: EffectComposer;
    private animationId: number | null = null;
    
    // Scene objects
    private trackMesh: THREE.Mesh | null = null;
    private carMeshes: Map<string, THREE.Mesh> = new Map();
    private gridHelper: THREE.GridHelper | null = null;

    constructor(config: Track3DConfig) {
        // 1. Initialize Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(config.isDarkTheme ? 0x111111 : 0xf0f0f0);
        this.scene.fog = new THREE.Fog(config.isDarkTheme ? 0x111111 : 0xf0f0f0, 100, 1000);

        // 2. Initialize Camera
        this.camera = new THREE.PerspectiveCamera(
            60, 
            config.width / config.height, 
            0.1, 
            5000
        );
        this.camera.position.set(0, 50, 50);

        // 3. Initialize Renderer
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true 
        });
        this.renderer.setSize(config.width, config.height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        config.container.appendChild(this.renderer.domElement);

        // 4. Initialize Controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;

        // 5. Initialize Post-Processing
        this.composer = new EffectComposer(this.renderer);
        const renderPass = new RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);

        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(config.width, config.height),
            1.5, // Strength
            0.4, // Radius
            0.85 // Threshold
        );
        this.composer.addPass(bloomPass);

        // 6. Add Lighting
        this.setupLighting();

        // 7. Add Helpers
        this.gridHelper = new THREE.GridHelper(1000, 100, 0x444444, 0x222222);
        this.scene.add(this.gridHelper);

        // Start loop
        this.animate();
    }

    private setupLighting() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(100, 100, 50);
        dirLight.castShadow = true;
        dirLight.shadow.mapSize.width = 2048;
        dirLight.shadow.mapSize.height = 2048;
        this.scene.add(dirLight);
    }

    public updateDimensions(width: number, height: number) {
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
        this.composer.setSize(width, height);
    }

    public updateCarPosition(driverId: string, position: { x: number, y: number, z: number }) {
        let carMesh = this.carMeshes.get(driverId);
        
        if (!carMesh) {
            // Create new car mesh if not exists
            const geometry = new THREE.BoxGeometry(2, 1, 4);
            const material = new THREE.MeshStandardMaterial({ color: 0xff0000 });
            carMesh = new THREE.Mesh(geometry, material);
            carMesh.castShadow = true;
            this.scene.add(carMesh);
            this.carMeshes.set(driverId, carMesh);
        }

        // Update position (convert iRacing coords to Three.js coords if needed)
        // iRacing: X = East/West, Y = Up/Down, Z = North/South
        // Three.js: X = Right, Y = Up, Z = Forward
        carMesh.position.set(position.x, position.y, position.z);
    }

    public renderTrack(coordinates: { x: number, y: number, z: number }[]) {
        if (this.trackMesh) {
            this.scene.remove(this.trackMesh);
        }

        if (coordinates.length < 2) return;

        const points = coordinates.map(c => new THREE.Vector3(c.x, c.y, c.z));
        const curve = new THREE.CatmullRomCurve3(points);
        const geometry = new THREE.TubeGeometry(curve, coordinates.length * 2, 5, 8, false);
        const material = new THREE.MeshStandardMaterial({ 
            color: 0x333333,
            roughness: 0.8,
            metalness: 0.2
        });

        this.trackMesh = new THREE.Mesh(geometry, material);
        this.trackMesh.receiveShadow = true;
        this.scene.add(this.trackMesh);
    }

    private animate = () => {
        this.animationId = requestAnimationFrame(this.animate);
        this.controls.update();
        // this.renderer.render(this.scene, this.camera);
        this.composer.render();
    }

    public dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.renderer.dispose();
        this.controls.dispose();
        // Dispose geometries and materials...
    }
}
