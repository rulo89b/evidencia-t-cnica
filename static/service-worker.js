
const CACHE_NAME = "evidencia-tecnica-v1";

const STATIC_ASSETS = [
    "/static/css/app.css",
    "/static/icons/icon-192.png",
    "/static/icons/icon-512.png",
    "/static/js/pwa.js",
    "/static/manifest.json",
    "/static/offline.html",
];

// Instalar el Service Worker.
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
});

// Eliminar versiones anteriores de nuestra caché.
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys
                    .filter((key) =>
                        key.startsWith("evidencia-tecnica-") &&
                        key !== CACHE_NAME
                    )
                    .map((key) => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

// Interceptar solicitudes.
self.addEventListener("fetch", (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // No interceptar formularios ni otras operaciones.
    if (request.method !== "GET") {
        return;
    }

    // No interceptar recursos externos.
    if (url.origin !== self.location.origin) {
        return;
    }

    // Las páginas siempre se solicitan al servidor.
    if (request.mode === "navigate") {
        event.respondWith(
            fetch(request, { cache: "no-store" })
                .catch(async () => {
                    const cache = await caches.open(
                        CACHE_NAME
                    );

                    return (
                        await cache.match(
                            "/static/offline.html"
                        )
                    ) || Response.error();
                })
        );

        return;
    }

    // Solo almacenar recursos estáticos autorizados.
    if (STATIC_ASSETS.includes(url.pathname)) {
        event.respondWith(
            caches.open(CACHE_NAME).then(
                async (cache) => {
                    try {
                        const response = await fetch(request);

                        if (response.ok) {
                            await cache.put(
                                request,
                                response.clone()
                            );
                        }

                        return response;

                    } catch (error) {
                        return (
                            await cache.match(request)
                        ) || Response.error();
                    }
                }
            )
        );
    }
});
