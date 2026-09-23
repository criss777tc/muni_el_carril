// ====================================================
//  PARALLAX del video
// ====================================================
const parallax = document.querySelector('.video-bg');
let isAnimating = false;

function updateParallax() {
    const scrollY = window.scrollY;
    const maxScroll = 400;
    const progress = Math.min(scrollY / maxScroll, 1);
    const scale = 1 + progress * 5;
    const opacity = 1 - progress;
    if (parallax) {
        parallax.style.transform = `scale(${scale})`;
        parallax.style.opacity = opacity;
    }
    isAnimating = false;
}

window.addEventListener('scroll', () => {
    if (!isAnimating) {
        isAnimating = true;
        requestAnimationFrame(updateParallax);
    }
});

// ====================================================
//  CONSTANTES
// ====================================================
const API_BASE = 'http://localhost:5000/api';

// Construye la URL pública de una imagen guardada por la API.
// Si la ruta ya es una URL completa (http/https) la devuelve tal cual;
// si es una ruta relativa tipo "static/imagenes/…" la prefija con el host.
function imagenUrl(ruta) {
    if (!ruta) return 'https://picsum.photos/seed/fallback/900/600';
    if (ruta.startsWith('http')) return ruta;
    return `${API_BASE.replace('/api', '')}/${ruta}`;
}

// ====================================================
//  CARGAR NOTICIAS DESDE LA BD
// ====================================================
document.addEventListener('DOMContentLoaded', async () => {
    // ── CARRUSEL: carga desde tabla "noticias" ──
    try {
        const res = await fetch(`${API_BASE}/noticias`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const noticias = await res.json();
        noticias.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
        renderCarrusel(noticias);
    } catch (err) {
        console.error('Error al cargar noticias (carrusel):', err);
    }

    // ── NOVEDADES: carga desde tabla "eventos" ──
    try {
        const res = await fetch(`${API_BASE}/eventos`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const eventos = await res.json();
        // La API ya los devuelve ordenados por fecha DESC
        renderNovedades(eventos);
    } catch (err) {
        console.error('Error al cargar eventos (novedades):', err);
    }
});


// ====================================================
//  RENDER — SECCIÓN NOVEDADES (desde tabla "eventos")
//  Collage: el 1er evento → tarjeta grande (izquierda)
//           los 4 siguientes → tarjetas chicas (derecha)
//  Se genera dinámicamente según los datos de la BD.
// ====================================================
function renderNovedades(eventos) {
    const collage = document.getElementById('collage-novedades');
    if (!collage) return;

    collage.innerHTML = '';

    if (eventos.length === 0) {
        collage.innerHTML = '<p style="color:#666;">No hay novedades por el momento.</p>';
        return;
    }

    // ── Tarjeta grande: el evento más nuevo ──
    const e = eventos[0];
    const grande = document.createElement('div');
    grande.className = 'tarjeta-grande' + (e.imagen ? '' : ' sin-imagen');
    if (e.imagen) grande.style.backgroundImage = `url('${imagenUrl(e.imagen)}')`;
    grande.innerHTML = `
        <div class="texto">
            <h2>${e.nombre}</h2>
            <p>${e.descripcion || ''}</p>
        </div>
    `;
    collage.appendChild(grande);

    // ── Tarjetas chicas: los 4 eventos siguientes ──
    const chicas = document.createElement('div');
    chicas.className = 'chicas';

    const chicasEventos = eventos.slice(1, 5); // máximo 4
    chicasEventos.forEach(ev => {
        const chica = document.createElement('div');
        chica.className = 'tarjeta-chica' + (ev.imagen ? '' : ' sin-imagen');
        if (ev.imagen) chica.style.backgroundImage = `url('${imagenUrl(ev.imagen)}')`;
        chica.innerHTML = `
            <div class="texto">
                <h3>${ev.nombre}</h3>
            </div>
        `;
        chicas.appendChild(chica);
    });

    collage.appendChild(chicas);
}

// ====================================================
//  RENDER — CARRUSEL
//  Usa TODAS las noticias (cada una es un slide).
// ====================================================
let indiceActual = 0;
let totalSlides = 0;

function renderCarrusel(noticias) {
    const pista = document.getElementById('pista');
    const puntos = document.getElementById('puntos');
    const noticiaNum = document.getElementById('noticia-num');
    if (!pista) return;

    totalSlides = noticias.length;
    if (totalSlides === 0) {
        pista.innerHTML = '<div class="elemento"><h2>No hay noticias</h2></div>';
        return;
    }

    // Generar slides
    pista.innerHTML = noticias.map(n => `
        <div class="elemento">
            ${n.imagen ? `<img src="${imagenUrl(n.imagen)}" alt="${n.nombre}">` : ''}
            <h2>${n.nombre}</h2>
            <p>${n.descripcion || ''}</p>
            <small>${n.fecha ? new Date(n.fecha).toLocaleDateString('es-AR') : ''}</small>
        </div>
    `).join('');

    // Generar puntos indicadores
    if (puntos) {
        puntos.innerHTML = noticias.map((_, i) =>
            `<button class="punto${i === 0 ? ' activo' : ''}" onclick="irA(${i})"></button>`
        ).join('');
    }

    // Número de noticia
    if (noticiaNum) noticiaNum.textContent = '1';

    indiceActual = 0;
    actualizarPosicion();
}

// ====================================================
//  NAVEGACIÓN DEL CARRUSEL
// ====================================================
function actualizarPosicion() {
    const pista = document.getElementById('pista');
    if (pista) {
        pista.style.transform = `translateX(-${indiceActual * 100}%)`;
    }

    // Actualizar puntos
    document.querySelectorAll('.punto').forEach((p, i) => {
        p.classList.toggle('activo', i === indiceActual);
    });

    // Actualizar número
    const noticiaNum = document.getElementById('noticia-num');
    if (noticiaNum) noticiaNum.textContent = indiceActual + 1;
}

function mover(dir) {
    if (totalSlides === 0) return;
    indiceActual = (indiceActual + dir + totalSlides) % totalSlides;
    actualizarPosicion();
}

function irA(i) {
    indiceActual = i;
    actualizarPosicion();
}