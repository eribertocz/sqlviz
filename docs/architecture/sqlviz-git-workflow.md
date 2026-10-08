# Flujo de Git

**Decisión del usuario — 2026-10-07:** el usuario autoriza de forma permanente
la gestión habitual de Git y delega en el agente el criterio sobre commits,
ramas, pushes y tags. Esta decisión sustituye la consulta individual anterior.
El agente debe explicar cuándo corresponde cada acción y por qué, sin pedir
de nuevo permiso para las operaciones habituales ya autorizadas.

## Trabajo habitual

1. Revisar estado, rama y cambios existentes; preservar trabajo del usuario.
2. Implementar un incremento y completar sus comprobaciones antes de
   registrarlo. Incluir documentación del contrato y límites relevantes.
3. Avisar que corresponde hacer commit, explicar su alcance y registrarlo cuando
   el incremento esté terminado y verificado. Comunicar el resultado y su hash.
4. Seleccionar archivos/hunks explícitos. Revisar el diff staged; evitar `git add .`
   y no incluir proyectos `.sqlviz`, secretos, builds ni artefactos de pruebas.
5. Verificar cada estado intermedio si se divide trabajo acumulado; cada commit
   debe instalarse y pasar sus checks sin depender de archivos aún sin registrar.

Trabajar en ramas de alcance claro, preservar `main` y revisar los cambios antes
de integrarlos. Hacer push de una rama verificada al remoto del proyecto cuando
corresponda respaldar el incremento y ejecutar CI; comprobar antes el destino y
los workflows que activa. Informar del resultado de CI sin darlo por aprobado
si aún está pendiente. No usar force push ni reescribir historial compartido.

La delegación habitual no autoriza descartar trabajo ajeno, borrar referencias
con trabajo sin integrar ni desplegar el producto. Consultar únicamente cuando
una operación destructiva, una reescritura o una publicación con alcance nuevo
necesite una decisión del usuario. No usar reset/clean para ordenar el árbol.

## Registro del árbol acumulado

**Estado:** división autorizada por el usuario y registrada el 2026-10-07.
La base es `7f59429`; `main` conserva ese commit. Los cambios acumulados se
registran en `feat/sqlviz-foundations`, por alcance y dependencia. Registrar
únicamente el módulo nuevo de composición habría dejado imports sin resolver
en la base, por lo que primero se incorporaron las unidades previas.

Orden de commits:

| Orden y commit | Alcance revisable |
| --- | --- |
| 1. `a75b595` — `feat(server): harden execution and project integrity` | Base Python acumulada E0 y E1: CLI/Quack, autorización, presupuestos, parámetros, repositorios, jerarquía y dimensiones; sus pruebas y documentos de unidades. En el router de composición incluye únicamente autorización y lectura segura de dimensiones, conservando el contrato previo en este estado intermedio |
| 2. `9bafd1a` — `feat(web): streamline dashboard navigation and filter context` | Cambios acumulados del frontend: navegación, selector de dashboards, filtros, runtime de lectura, dimensiones y sus pruebas; documentación UX, configuración Node y CI |
| 3. `a5e1e44` — `fix(api): validate dashboard composition requests` | Nuevo contrato/adaptador de composición, cambio tipado del router, 63 casos de contrato, ajuste de prueba de alcance para usar un resultado válido y documento del contrato |
| 4. `docs: align product architecture and delivery roadmap` | Auditoría y documentos estratégicos, índice, README, CHANGELOG, seguimiento del plan y este flujo de Git |

El cuarto commit es el que incorpora este registro; su hash se consulta en el
historial, para no introducir una referencia circular dentro del documento.

Los archivos compartidos se seleccionaron mediante una reconstrucción controlada
del index, conservando los archivos de trabajo. Se exportaron copias del index
para comprobar los estados intermedios con sus propios imports Python; ningún
test del primer commit dependió del contrato de composición aún sin registrar.
Las dependencias instaladas se reutilizaron para los checks locales; no se afirma
haber realizado una instalación nueva de cada entorno ni ejecutado CI remoto.

## Verificación del registro

- Primer estado: 1814 pruebas Python pasan inicialmente y 5 pruebas HTTP fallan
  por ausencia del build SPA. Después de compilar su frontend, esas 5 pasan:
  **1819 pruebas verificadas y 3 omitidas**. Ruff y mypy (130 archivos) pasan.
- Segundo estado: svelte-check sin errores/advertencias; **133 pruebas frontend**
  en 21 archivos y build correcto. Las 8 pruebas HTTP de login/archivos estáticos
  pasan con ese build. Las advertencias conocidas de teardown de Svelte y chunks
  grandes permanecen documentadas; no se las confunde con errores del check.
- Tercer estado: **191 pruebas** de composición, dimensiones, autorización,
  overrides y HTTP pasan. Ruff y mypy (131 archivos) pasan. La suite completa del
  árbol final Python ya había pasado **1882 pruebas, con 3 omitidas**, antes de
  dividir los commits; se conservaron los archivos de código sin modificaciones.
- Documentación: enlaces locales de los 29 Markdown cambiados comprobados y
  `git diff --check` sin errores.

El checkout limpio reveló una dependencia de las pruebas HTTP en el build.
La configuración de CI ahora genera y comprueba el SPA en `frontend`, comparte
su artefacto y lo descarga en los jobs Python antes de pytest. Esto sigue el
[flujo de artefactos entre jobs de GitHub Actions](https://docs.github.com/en/actions/tutorials/store-and-share-data).
Se comprobaron localmente el YAML, nombres/rutas, orden y fallo si falta el build;
la ejecución remota sigue pendiente.

Logs, manifests y copias de verificación están en `build/git-review`, ignorados
por Git. No se incluyeron proyectos `.sqlviz`, bases de aprendizaje ni builds en
los commits. En el registro inicial no se crearon tags ni se publicó en un remoto.

## Tags y releases

Un incremento interno no necesita tag. Proponer un tag cuando se prepare una
versión publicable, con versión consistente, changelog, build, migraciones si
corresponde y CI verificados. Preferir un tag anotado sobre el commit exacto del
release. Explicar cuándo corresponde y registrar su nombre, alcance y evidencia.
La autorización de Git incluye los tags de versiones preparadas del proyecto;
desplegar o publicar un release en otro canal requiere autorización propia.
