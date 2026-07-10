/* ============================================================
   ARENA ANIMATION ENGINE — GSAP + Three.js + Lenis
   ============================================================ */

// ========== 1. LENIS SMOOTH SCROLL ==========
function initLenis() {
    if (typeof Lenis !== 'undefined') {
        const lenis = new Lenis({
            duration: 1.4,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
            smoothWheel: true,
        });
        function raf(time) {
            lenis.raf(time);
            requestAnimationFrame(raf);
        }
        requestAnimationFrame(raf);
        return lenis;
    }
    return null;
}

// ========== 2. GSAP ANIMATIONS ==========
function initGSAPAnimations() {
    if (typeof gsap === 'undefined') return;

    const heroTitle = document.querySelector('.hero-animate-title');
    if (heroTitle) {
        gsap.from(heroTitle, {
            y: 100, opacity: 0, duration: 1.2,
            ease: 'power4.out', delay: 0.3
        });
    }
    const heroSubtitle = document.querySelector('.hero-animate-subtitle');
    if (heroSubtitle) {
        gsap.from(heroSubtitle, {
            y: 60, opacity: 0, duration: 1,
            ease: 'power3.out', delay: 0.6
        });
    }
    const heroCta = document.querySelectorAll('.hero-animate-cta');
    if (heroCta.length) {
        gsap.from(heroCta, {
            y: 40, opacity: 0, duration: 0.8,
            ease: 'power3.out', delay: 0.9, stagger: 0.15
        });
    }
}

// ========== 3. THREE.JS BACKGROUND PARTICLES ==========
function initThreeParticles() {
    if (typeof THREE === 'undefined') return;
    const container = document.getElementById('three-canvas');
    if (!container) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 200;
    const posArray = new Float32Array(particlesCount * 3);
    for (let i = 0; i < particlesCount * 3; i += 3) {
        posArray[i] = (Math.random() - 0.5) * 20;
        posArray[i + 1] = (Math.random() - 0.5) * 20;
        posArray[i + 2] = (Math.random() - 0.5) * 20;
    }
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));

    const colorsArray = new Float32Array(particlesCount * 3);
    const colorOptions = [
        new THREE.Color(0xD90429), new THREE.Color(0xF4B400), new THREE.Color(0x0066FF)
    ];
    for (let i = 0; i < particlesCount; i++) {
        const c = colorOptions[Math.floor(Math.random() * colorOptions.length)];
        colorsArray[i * 3] = c.r; colorsArray[i * 3 + 1] = c.g; colorsArray[i * 3 + 2] = c.b;
    }
    particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colorsArray, 3));

    const particlesMaterial = new THREE.PointsMaterial({
        size: 0.04, transparent: true, opacity: 0.6,
        vertexColors: true, blending: THREE.AdditiveBlending,
    });
    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particlesMesh);
    camera.position.z = 8;

    let mouseX = 0, mouseY = 0;
    document.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX / window.innerWidth) * 2 - 1;
        mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    });

    function animate() {
        requestAnimationFrame(animate);
        particlesMesh.rotation.y += 0.0005;
        particlesMesh.rotation.x += 0.0003;
        particlesMesh.rotation.x += mouseY * 0.0002;
        particlesMesh.rotation.y += mouseX * 0.0002;
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

// ========== 4. INTERSECTION OBSERVER ==========
function initRevealObserver() {
    const options = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add('active');
        });
    }, options);
    document.querySelectorAll('.reveal-fade, .reveal-scale, .reveal-left, .reveal-right, .stagger-children').forEach(el => {
        observer.observe(el);
    });
}

// ========== 5. MAGNETIC BUTTON EFFECT ==========
function initMagneticButtons() {
    document.querySelectorAll('.btn-magnetic').forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            btn.style.transform = `translate(${(e.clientX - rect.left - rect.width/2) * 0.3}px, ${(e.clientY - rect.top - rect.height/2) * 0.3}px)`;
        });
        btn.addEventListener('mouseleave', () => { btn.style.transform = 'translate(0,0)'; });
    });
}

// ========== 6. INTERACTIVE HERO GLOW ==========
function initHeroGlow() {
    const hero = document.querySelector('.hero-section');
    const glow = document.getElementById('heroGlow');
    if (!hero || !glow) return;
    glow.style.cssText = `position:absolute;width:400px;height:400px;border-radius:50%;background:radial-gradient(circle,rgba(217,4,41,0.12) 0%,transparent 70%);pointer-events:none;filter:blur(60px);z-index:2;opacity:0;transition:opacity 0.5s ease;`;
    hero.addEventListener('mousemove', (e) => {
        const rect = hero.getBoundingClientRect();
        glow.style.opacity = '1';
        glow.style.left = (e.clientX - rect.left - 200) + 'px';
        glow.style.top = (e.clientY - rect.top - 200) + 'px';
    });
    hero.addEventListener('mouseleave', () => { glow.style.opacity = '0'; });
}

// ========== 7. PRELOADER ==========
function initPreloader() {
    const preloader = document.getElementById('preloader');
    if (!preloader) return;
    window.addEventListener('load', () => {
        setTimeout(() => {
            preloader.style.opacity = '0';
            setTimeout(() => { preloader.style.visibility = 'hidden'; }, 800);
        }, 2500);
    });
}

// ========== 8. CONFETTI ==========
function createConfettiBurst() {
    for (let i = 0; i < 50; i++) {
        const c = document.createElement('div');
        c.style.cssText = `position:fixed;top:-10px;left:${Math.random()*100}vw;width:${Math.random()*8+4}px;height:${Math.random()*8+4}px;background:${Math.random()>0.5?'#D90429':'#F4B400'};z-index:99999;pointer-events:none;animation:confettiFall ${Math.random()*2+2}s linear forwards;`;
        document.body.appendChild(c);
        setTimeout(() => c.remove(), 4000);
    }
}

// ========== 9. TOAST ==========
function showArenaToast(msg, type) {
    const colors = {success:'linear-gradient(135deg,#D90429,#F4B400)', info:'linear-gradient(135deg,#0066FF,#7C3AED)', error:'linear-gradient(135deg,#D90429,#8B0000)'};
    const t = document.createElement('div');
    t.style.cssText = `position:fixed;bottom:30px;right:30px;background:${colors[type]||colors.success};color:white;padding:16px 28px;border-radius:16px;font-weight:600;font-size:0.9rem;z-index:100000;box-shadow:0 10px 40px rgba(0,0,0,0.5);transform:translateY(20px);opacity:0;transition:all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);`;
    t.innerHTML = `<i class="fas fa-check-circle me-2"></i> ${msg}`;
    document.body.appendChild(t);
    requestAnimationFrame(() => { t.style.opacity = '1'; t.style.transform = 'translateY(0)'; });
    setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateY(20px)'; setTimeout(() => t.remove(), 400); }, 3000);
}

// ========== 10. COUNTDOWN ==========
function initCountdown(targetStr) {
    const target = new Date(targetStr).getTime();
    if (isNaN(target)) return;
    setInterval(() => {
        const diff = target - Date.now();
        if (diff <= 0) return;
        const d = Math.floor(diff/(86400000));
        const h = Math.floor((diff%(86400000))/(3600000));
        const m = Math.floor((diff%(3600000))/(60000));
        const s = Math.floor((diff%(60000))/1000);
        ['days','hours','mins','secs'].forEach((id,i) => {
            const el = document.getElementById(id);
            if (el) el.innerText = [d,h,m,s][i].toString().padStart(2,'0');
        });
    }, 1000);
}

// ========== INIT ==========
document.addEventListener('DOMContentLoaded', function() {
    initLenis();
    initGSAPAnimations();
    initThreeParticles();
    initRevealObserver();
    initMagneticButtons();
    initHeroGlow();
    initPreloader();

    const cd = document.getElementById('countdown');
    if (cd && cd.dataset.target) initCountdown(cd.dataset.target);
});
