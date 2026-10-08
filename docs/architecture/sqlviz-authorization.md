# Autorización de autor y lectores

**Implementado:** 2026-10-06, en el árbol de trabajo; sin release ni commit nuevo.
**Alcance:** segunda unidad de E0: autorización HTTP por recurso y solicitud.
Incluye puntos 2/3 y sesiones/cursores del punto 5. El aislamiento SQL se incorpora
después en la [tercera unidad](sqlviz-analytical-execution.md).

## Política

Cada `create_app()` crea su propio `AuthorizationService`, con almacenes distintos
para sesiones administrativas y de lector. Reiniciar los invalida. No hay sesiones
globales entre aplicaciones.

| Operación | Autor | Lector de dashboard | Lector de workspace | Anónimo |
| --- | --- | --- | --- | --- |
| CRUD, overrides, crear/revocar enlaces y configuración | Permitido | Rechazado | Rechazado | 401 |
| Listado general de dashboards/carpetas | Permitido | Rechazado | Usa `/view/workspace/{token}` | 401 |
| Listar paneles | Permitido | Solo su dashboard | Dashboard existente | 401 |
| Consultar/ejecutar panel y dominios de filtros | Permitido | Solo su dashboard | Panel de dashboard existente | 401 |
| Componer layout | Permitido | Cada panel debe estar en su alcance | Cada panel debe existir en el workspace | 401 |
| Versión/build y shell de login/viewer | Público, sin datos de proyecto | Público | Público | Público |

Demo conserva autoría sin contraseña. Si una solicitud declara un enlace, ese
alcance prevalece incluso en demo o con cookie administrativa. No concede
escritura; una solicitud administrativa sin esa cabecera conserva sus permisos.

## Credenciales por solicitud

Las URLs de datos se conservan. Ambos viewers envían `X-SQLviz-Share` en listados
de paneles, ejecución, dominios y composición. El backend consulta la fila real
del enlace, verifica firma/secreto vigente y revocación, y comprueba el recurso.
IDs inexistentes o fuera de alcance devuelven 404; un lector debe indicar
`dashboard_id` al listar paneles, incluso en workspace.

- **Público:** el token concede lectura de su alcance.
- **Privado:** requiere además una sesión administrativa válida; las llamadas
  siguen limitadas al enlace, como preview.
- **Contraseña:** el endpoint `/unlock` verifica el password y añade
  `viewer_session` al payload existente. Las llamadas posteriores envían también
  `X-SQLviz-Viewer-Session`.

La sesión de lector está ligada al token exacto y a esa aplicación; no desbloquea
otros enlaces. Revocar borra las sesiones de ese enlace. Rehabilitar el share no
rehabilita sesiones anteriores. Rotar el secreto invalida enlaces y limpia las
sesiones de lector.

Almacenes con ventana deslizante de 24 h, reloj monotónico y lock para operaciones
de crear/comprobar/renovar/revocar. Cookie administrativa HttpOnly, SameSite Strict
y Secure cuando la URL de solicitud usa HTTPS. Cambiar la contraseña invalida las
sesiones administrativas de esa aplicación. La cookie dura 24 h desde el login;
no se renueva en cada lectura.

El cliente de viewer es por componente y conserva su sesión solo en memoria.
No escribe credenciales en localStorage. Recargar un enlace protegido vuelve a
pedir contraseña. Respuestas de API/viewer: `Cache-Control: no-store`.
Si una solicitud de navegación, ejecución o dominios pierde autorización, el
viewer retira resultados y muestra el error. No hay push de revocación ni forma
de retirar datos que un cliente ya recibió. Los errores ordinarios de consulta
conservan el comportamiento previo; estados de datos anteriores y carreras son E1.

## Ejecución y arquitectura

Un lector ejecuta únicamente el SQL guardado del panel con valores enlazados de
filtros. La política exige un query parseable; rechaza múltiples sentencias,
DDL/DML, SELECT INTO y modificaciones en CTEs. Usa el parser para comentarios
finales y puntos y coma dentro de strings, no separación textual por `;`.

Ejecutar como lector no guarda inferencias, clasificación de dashboard ni eventos
de aprendizaje. Conserva overrides del autor en la respuesta. Todavía recalcula
inferencia; consumir especificaciones publicadas/versionadas pertenece a E1/E2.

| Módulo | Responsabilidad |
| --- | --- |
| `services/access.py` | Principal, sesiones y alcance de recursos, sin importar FastAPI |
| `services/query_policy.py` | Elegibilidad de sentencias, sin prometer sandbox |
| `security.py` | Credenciales HTTP y traducción de errores 401/403/404 |
| `main.py` | Servicio por aplicación y protección de routers administrativos |
| Routers | Comprobar recurso antes de leer/ejecutar; respetar el modo lector |
| `dependencies.py` | Cursor por solicitud, cerrado también ante errores |
| `viewerApi.ts` | Credenciales por viewer y comunicación de rechazo de acceso |

El servicio recibe DuckDB prestado por operación; no se introduce un repositorio
genérico ni migración del formato para este incremento. `QuackConnectionRouter`
permanece como selector legado, consultando el almacén local; las rutas HTTP no
lo usan como frontera de seguridad.

## Límites pendientes

La autorización HTTP no limita por sí sola lo que puede hacer SELECT. La
[tercera unidad](sqlviz-analytical-execution.md) incorpora catálogo independiente,
restricciones del motor y presupuestos; el AST no sustituye esos controles.
No equivale a aislamiento de proceso ni habilita todavía adaptadores externos.

La [cuarta unidad](sqlviz-parameters-and-quality.md) corrige tipos, advertencias
de svelte-check y alineación de runtime/metadata. Quedan operación/rate limiting,
diagnósticos de dependencias frontend y políticas de datasets. Este incremento
corrige accesos HTTP anónimos y alcance del enlace; no certifica SQL arbitrario,
datos reales o despliegue público.

## Validación

- Suite Python completa: **1497 pasan, 3 omitidos**, en 151,66 s; incluye **78
  casos nuevos** de servicio/autorización. Comando local:
  `.venv/Scripts/python.exe -m pytest --tb=short -q --basetemp build/access-review/pytest-final-01`.
  Se preparó un directorio de pruebas dedicado; pytest puede borrar el contenido
  de `--basetemp` al reutilizarlo. No usar una carpeta con datos personales.
- Matriz con API real y bases en memoria, sin overrides de autorización: anónimos,
  alcance entre dashboards, mutaciones, composición, filtros, públicos/privados/
  contraseña, revocación/rehabilitación, rotación, expiración y aplicaciones distintas.
- Servicio probado sin HTTP, con sesiones concurrentes y política de sentencias.
  Snapshots verifican que el lector no modifica paneles, dashboards ni aprendizaje.
- **72 tests frontend en 11 archivos**, cliente por viewer y pruebas de desbloqueo/
  rechazo de ambos viewers. `svelte-check`: 0 errores, 6 advertencias previas.
- `ruff` correcto; tipos API/CLI correctos. El chequeo global mantiene un error de
  inference; el error de auth desaparece al retirar el almacén global.
- Build estático correcto, con advertencias previas de bundles y sourcemaps/PURE.
- Chromium con el build de producción y FastAPI real, sin mocks de API: login
  obligatorio para autoría, dashboard/workspace públicos y con contraseña,
  rechazo de contraseña incorrecta antes de pedir datos, gráficos renderizados,
  credenciales en cada solicitud y retirada de gráficos tras revocar y solicitar
  datos de nuevo. **Sin errores de página** en esos cuatro flujos de viewer.
  Servidor/brain de ensayo en memoria; reporte y capturas locales en
  `build/access-review/`, ignorados por git. El servidor de ensayo se detuvo;
  no se reinició ni vació la demo que el usuario tenía abierta.

Validación local en Windows/Python 3.13; no sustituye CI Python 3.12 ni pruebas
exhaustivas en otros navegadores. Los fixtures de CRUD son autores con sesiones
reales del almacén; los casos negativos no tienen sesión. No se cambió a demo
para permitir acceso a proyectos protegidos.
