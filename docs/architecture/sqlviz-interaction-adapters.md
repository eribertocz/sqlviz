# GridStack y Drawflow: adaptadores de interacción

**Decisión solicitada por el usuario:** 2026-10-08.
**Estado entregado:** dependencias fijadas y adaptadores internos con pruebas.
**Pendiente:** conexión al Studio/viewer, persistencia del lienzo y mapa de objetos
reales. Este incremento no habilita drag/resize ni un mapa en la aplicación.

| Biblioteca | Versión fijada | Responsabilidad |
| --- | --- | --- |
| GridStack | 14.0.0 | Renderizado/interacción del lienzo de doce columnas, a integrar en S1/S2 |
| Drawflow | 0.0.60 | Representación visual del mapa de dependencias, a integrar en F2/S4.6a |
| Tipos Drawflow | @types/drawflow 0.0.12 | Tipado del límite JavaScript; dependencia de desarrollo |

Ambas bibliotecas declaran licencia MIT. Las versiones se verificaron en npm y
quedaron fijadas en manifest/lockfile; no copiar la versión antigua del encabezado
de la landing de GridStack. Referencias oficiales: [GridStack](https://gridstackjs.com/),
[opciones actuales](https://gridstackjs.com/doc/html/interfaces/GridStackOptions.html),
[motor GridStack](https://gridstackjs.com/doc/html/classes/GridStackEngine.html),
[Drawflow](https://github.com/jerosoler/Drawflow).

## Límites de arquitectura

SQLviz conserva identidad, configuración, layout confirmado, revisiones, permisos
y publicación. Las bibliotecas son adaptadores web; no reemplazan esos contratos
con sus exports. No crean datasets, infieren gráficos ni ejecutan SQL.

Carga dinámica bajo demanda en navegador, sin evaluar estas bibliotecas al
importar el módulo de adaptación en servidor. Svelte mantiene los componentes de
gráficos; GridStack administra su envolvente de posición/gesto. Drawflow recibe
metadata autorizada y selección; los editores del Studio mantienen las escrituras.
No compartir instancias o registros de objetos entre dashboards/sesiones.

## Proyección de geometría GridStack

El [adaptador interno](../../packages/sqlviz-web/src/lib/integrations/gridstackCanvas.ts)
convierte posiciones S0 a widgets identificados. Una fila del motor equivale a un
píxel CSS: `cellHeight: 1`, `margin: 0`, `mode: 'float'`, doce columnas. `h` incluye
altura de contenido más gap final; `y` representa `top_px`. No imponer filas
de 50/100 px ni convertir una altura de 301 px en un múltiplo de esas filas.

La integración DOM debe reservar gap a derecha/abajo de cada contenido y usar
ancho del contenedor de columnas más gap. Eso preserva el ancho visible S0. El
padding pertenece al canvas exterior. Descontar la reserva final al dimensionar
el lienzo para que no introduzca scroll adicional en modo pantalla. Esta proyección
no es un segundo formato de guardado.

`loadCanvasEngineClass(gapPx)` devuelve una clase por adaptador, sin registro
global. Movimiento/resize rechaza colisiones, fuera de límites y tamaños menores
antes del clamping nativo; no empuja vecinos ni solicita packing. `mode: 'float'`
por sí solo no bloquea el empuje nativo por colisión. La carga debe partir de una
proyección validada, sin reparar documentos persistidos por compactación automática.

La conversión inversa conserva el orden de IDs del documento, rechazando IDs
duplicados, faltantes o desconocidos. Excluye HTML y metadata del motor del
candidato. El servidor sigue validando el documento completo antes de guardar.
Este adaptador inicial proyecta paneles con mínimo de 120 px; texto/mínimos por
tipo requieren la extensión S1.2/S1.3, todavía pendiente.

GridStack soporta filas, handles y eventos; las guías de bordes, medidas, magnetismo
controlable y accesibilidad de SQLviz no se consideran entregadas por instalarlo.
En S2, un gesto produce un borrador y una entrada de undo; Escape, conflictos y
fallos conservan el estado previo. No persistir cada evento `change`.

## Proyección de mapa Drawflow

El [adaptador interno](../../packages/sqlviz-web/src/lib/integrations/drawflowMap.ts)
monta nodos/aristas recibidos, con IDs del producto separados de IDs del renderer.
Conserva inputs nombrados aunque Drawflow use puertos por índice. Un dataset
reutilizado sigue siendo un único nodo con salidas hacia varios consumidores.

Usa modo `fixed` para bloquear conexiones/borrados nativos y mantener navegación.
Cada etiqueta es un botón que selecciona el objeto mediante callback, operable
por teclado; el mapa/contexto completo y la alternativa en lista F2 siguen
pendientes. Usa plantilla constante y `textContent`, sin interpretar labels/SQL
como HTML. No importar exports arbitrarios de Drawflow al dominio.

Valida referencias, duplicados y presupuestos antes de tocar el host. El llamador
debe suministrar la proyección autorizada F1; esta comprobación no acredita
permisos ni descubre dependencias. No interpreta resultados de ejecución.

Una instancia vive en un subárbol privado: cancelación durante carga no lo monta;
dispose/abort elimina ese subárbol y callbacks sin borrar contenido del llamador.
Drawflow 0.0.60 no aporta `destroy`; su `clear` vacía nodos, y retirar el contenedor
privado permite liberar sus listeners. Reapertura usa otra instancia.
Actualización incremental con foco/zoom, layout automático, posiciones privadas,
grafos grandes y navegación completa se verifican en F2/F3.

## Evidencia y siguiente integración

Dieciséis [pruebas de adaptación](../../packages/sqlviz-web/src/lib/integrations/gridstackCanvas.test.ts)
y [Drawflow](../../packages/sqlviz-web/src/lib/integrations/drawflowMap.test.ts) usan
las bibliotecas reales: composición asimétrica, píxel exacto, espacio intencional,
colisión sin empuje, límites/identidad, reutilización e inputs, etiquetas como
texto, Delete/contextmenu, cancelación, dispose/reapertura y guardas de servidor.
Los adaptadores no acceden a proyectos reales.

Validación local: 197 pruebas frontend pasan (16 específicas de adaptación),
Svelte-check sin errores/advertencias, build de aplicación y build independiente
de los adaptadores. Los módulos de ese build se importan en Node sin evaluar DOM
y rechazan crear instancias fuera de navegador.

Chromium 1440×1100, fixture sin backend: ancho visible 592 px en un canvas útil de
1200 px, alturas 616/300/300 px y cambio exacto a 617 px; colisión sin cambiar
vecinos. Mapa de tres nodos/dos enlaces, etiqueta literal, selección y desmontaje;
contenedor de 400 px verificado para evitar renderizado con alto cero. Sin errores
JS. Artefactos bajo `build/interaction-adapters-review/`, ignorados por Git. Es
evidencia de compatibilidad, no acabado visual del producto ni ensayo de drag/touch.

`npm audit` reportó 11 avisos en otras dependencias ya existentes; no reportó
entradas para GridStack, Drawflow o sus tipos en esa corrida. No se actualizan esas
dependencias fuera de alcance. Persisten las advertencias conocidas de teardown
Svelte y tamaño de chunks. CI se comprueba sobre el commit enviado.

S1.1b.1 entrega el [núcleo de reconciliación](sqlviz-sql-identity-reconciliation.md);
S1.1b.2 integra asociaciones en el borrador como próximo incremento del producto.
S1.2d integra el contenedor
GridStack con referencias estables; S2 incorpora gestos/guías y guardado sobre ese
contrato. F1 precede el mapa visible Drawflow F2/S4.6a. La elección de bibliotecas
no salta reconciliación, revisiones ni autorización.
