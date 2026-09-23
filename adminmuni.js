// ==========================================================
// DASHBOARD — CRUD para Noticias y Eventos
// ==========================================================

const API_BASE = 'http://localhost:5000/api';

// ==========================================================
// SESIÓN
// ==========================================================

const token = localStorage.getItem('token');
const usuario = localStorage.getItem('usuario');

if (!token) {
    window.location.href = 'admin2.html';
}

document.getElementById('nombreUsuario').textContent = usuario || 'Admin';

// ==========================================================
// ESTADO
// ==========================================================

let tabActual = 'noticias';   // 'noticias' | 'eventos'
let editandoId = null;        // null = crear, number = editar
let eliminandoId = null;      // id del item a eliminar

// ==========================================================
// UTILIDADES
// ==========================================================

function imagenUrl(ruta) {
    if (!ruta) return null;
    if (ruta.startsWith('http')) return ruta;
    return `${API_BASE.replace('/api', '')}/${ruta}`;
}

function mostrarToast(mensaje, tipo = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast--${tipo}`;
    toast.textContent = mensaje;
    container.appendChild(toast);

    setTimeout(() => toast.remove(), 3200);
}

function formatearFecha(fechaStr) {
    if (!fechaStr) return '—';
    try {
        const d = new Date(fechaStr);
        return d.toLocaleDateString('es-AR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    } catch {
        return fechaStr;
    }
}

// ==========================================================
// TABS
// ==========================================================

document.querySelectorAll('.dash-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.dash-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        tabActual = tab.dataset.tab;
        document.getElementById('seccionTitulo').textContent =
            tabActual === 'noticias' ? 'Noticias' : 'Eventos';
        cargarDatos();
    });
});

// ==========================================================
// CARGAR DATOS
// ==========================================================

async function cargarDatos() {
    const cuerpo = document.getElementById('tablaCuerpo');
    const vacio = document.getElementById('mensajeVacio');
    const tabla = document.getElementById('tablaDatos');

    cuerpo.innerHTML = '';

    try {
        const res = await fetch(`${API_BASE}/${tabActual}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const datos = await res.json();

        if (datos.length === 0) {
            tabla.style.display = 'none';
            vacio.style.display = '';
            return;
        }

        tabla.style.display = '';
        vacio.style.display = 'none';

        datos.forEach(item => {
            const tr = document.createElement('tr');

            const id = item.id || item.id_eventos;
            const nombre = item.nombre || item.nombre_eventos || '';
            const imagen = item.imagen || item.imagen_eventos || null;
            const desc = item.descripcion || item.descripcion_eventos || '';
            const fecha = item.fecha || item.fecha_eventos || '';

            const imgUrl = imagenUrl(imagen);

            tr.innerHTML = `
                <td><strong>${id}</strong></td>
                <td>
                    ${imgUrl
                        ? `<img src="${imgUrl}" alt="${nombre}" class="table-img">`
                        : `<div class="table-img-placeholder">SIN IMG</div>`
                    }
                </td>
                <td>${nombre}</td>
                <td class="table-desc" title="${desc}">${desc}</td>
                <td>${formatearFecha(fecha)}</td>
                <td>
                    <div class="table-actions">
                        <button class="btn--icon edit" title="Editar" onclick="abrirEditar(${id}, '${nombre.replace(/'/g, "\\'")}', '${desc.replace(/'/g, "\\'")}', '${fecha}', '${imagen || ''}')">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"/>
                                <path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5z"/>
                            </svg>
                        </button>
                        <button class="btn--icon delete" title="Eliminar" onclick="abrirEliminar(${id}, '${nombre.replace(/'/g, "\\'")}')">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
                                <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1h2.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
                            </svg>
                        </button>
                    </div>
                </td>
            `;

            cuerpo.appendChild(tr);
        });

    } catch (error) {
        console.error('Error al cargar datos:', error);
        mostrarToast('Error al cargar los datos', 'error');
        tabla.style.display = 'none';
        vacio.style.display = '';
    }
}

// Cargar al inicio
document.addEventListener('DOMContentLoaded', cargarDatos);

// ==========================================================
// MODAL CREAR / EDITAR
// ==========================================================

const modalOverlay = document.getElementById('modalOverlay');
const formItem = document.getElementById('formItem');

function abrirModal() {
    modalOverlay.classList.add('open');
}

function cerrarModal() {
    modalOverlay.classList.remove('open');
    formItem.reset();
    document.getElementById('itemId').value = '';
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('filePlaceholder').style.display = '';
    editandoId = null;
}

// Botón "Agregar nuevo"
document.getElementById('btnNuevo').addEventListener('click', () => {
    editandoId = null;
    document.getElementById('modalTitulo').textContent =
        `Agregar ${tabActual === 'noticias' ? 'Noticia' : 'Evento'}`;
    cerrarModal(); // limpia
    abrirModal();
});

// Cerrar modal
document.getElementById('btnCerrarModal').addEventListener('click', cerrarModal);
document.getElementById('btnCancelar').addEventListener('click', cerrarModal);
modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) cerrarModal();
});

// Preview de imagen seleccionada
document.getElementById('itemImagen').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (ev) => {
            const preview = document.getElementById('imagePreview');
            preview.src = ev.target.result;
            preview.style.display = 'block';
            document.getElementById('filePlaceholder').style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
});

// Abrir modal para editar
function abrirEditar(id, nombre, descripcion, fecha, imagen) {
    editandoId = id;
    document.getElementById('modalTitulo').textContent =
        `Editar ${tabActual === 'noticias' ? 'Noticia' : 'Evento'}`;
    document.getElementById('itemId').value = id;
    document.getElementById('itemNombre').value = nombre;
    document.getElementById('itemDescripcion').value = descripcion;
    document.getElementById('itemFecha').value = fecha || '';

    // Mostrar imagen existente
    const preview = document.getElementById('imagePreview');
    const placeholder = document.getElementById('filePlaceholder');
    const imgUrl = imagenUrl(imagen);

    if (imgUrl) {
        preview.src = imgUrl;
        preview.style.display = 'block';
        placeholder.style.display = 'none';
    } else {
        preview.style.display = 'none';
        placeholder.style.display = '';
    }

    abrirModal();
}

// ==========================================================
// GUARDAR (CREAR O EDITAR)
// ==========================================================

formItem.addEventListener('submit', async (e) => {
    e.preventDefault();

    const nombre = document.getElementById('itemNombre').value.trim();
    const descripcion = document.getElementById('itemDescripcion').value.trim();
    const fecha = document.getElementById('itemFecha').value;
    const imagenFile = document.getElementById('itemImagen').files[0];

    if (!nombre || !descripcion) {
        mostrarToast('Nombre y descripción son obligatorios', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('nombre', nombre);
    formData.append('descripcion', descripcion);
    formData.append('fecha', fecha);
    if (imagenFile) {
        formData.append('imagen', imagenFile);
    }

    try {
        let url = `${API_BASE}/${tabActual}`;
        let method = 'POST';

        if (editandoId) {
            url = `${API_BASE}/${tabActual}/${editandoId}`;
            method = 'PUT';
        }

        const res = await fetch(url, {
            method,
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        const data = await res.json();

        if (res.ok) {
            mostrarToast(
                editandoId
                    ? 'Actualizado correctamente'
                    : 'Creado correctamente',
                'success'
            );
            cerrarModal();
            cargarDatos();
        } else {
            mostrarToast(data.error || 'Error al guardar', 'error');
        }

    } catch (error) {
        console.error('Error al guardar:', error);
        mostrarToast('Error de conexión con el servidor', 'error');
    }
});

// ==========================================================
// MODAL ELIMINAR
// ==========================================================

const deleteOverlay = document.getElementById('deleteOverlay');

function abrirEliminar(id, nombre) {
    eliminandoId = id;
    document.getElementById('deleteItemName').textContent = nombre;
    deleteOverlay.classList.add('open');
}

function cerrarDelete() {
    deleteOverlay.classList.remove('open');
    eliminandoId = null;
}

document.getElementById('btnCerrarDelete').addEventListener('click', cerrarDelete);
document.getElementById('btnCancelarDelete').addEventListener('click', cerrarDelete);
deleteOverlay.addEventListener('click', (e) => {
    if (e.target === deleteOverlay) cerrarDelete();
});

document.getElementById('btnConfirmarDelete').addEventListener('click', async () => {
    if (!eliminandoId) return;

    try {
        const res = await fetch(`${API_BASE}/${tabActual}/${eliminandoId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const data = await res.json();

        if (res.ok) {
            mostrarToast('Eliminado correctamente', 'success');
            cerrarDelete();
            cargarDatos();
        } else {
            mostrarToast(data.error || 'Error al eliminar', 'error');
        }

    } catch (error) {
        console.error('Error al eliminar:', error);
        mostrarToast('Error de conexión con el servidor', 'error');
    }
});

// ==========================================================
// LOGOUT
// ==========================================================

document.getElementById('btnLogout').addEventListener('click', async () => {
    try {
        await fetch(`${API_BASE}/logout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    } catch (error) {
        console.error(error);
    }

    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
    window.location.href = 'admin2.html';
});