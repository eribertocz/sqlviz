# SQLviz Dashboard Editing UX — v1.0

> **Estado:** Especificación oficial. Este documento define el diseño completo
> del flujo de edición de dashboards **antes** de implementar. Ninguna parte
> está implementada por el solo hecho de existir este documento — ver
> [Versión de implementación](#versión-de-implementación) para el fasing.

---

## Filosofía

El usuario nunca debe pensar en guardar.
Se concentra únicamente en escribir SQL, ejecutar y analizar resultados.

---

## Los 3 estados de un Dashboard

### 1. Draft

Lo que el usuario está editando ahora mismo.
Puede contener SQL incompleto o con errores.
SIEMPRE existe. Se guarda automáticamente.

**Auto-save triggers:**

- 2 segundos después de dejar de escribir
- Al cambiar de dashboard
- Al cerrar pestaña (`beforeunload`)
- Al perder foco del navegador

**Indicadores sutiles en el header:**

- `● Draft` → hay cambios sin guardar
- `Saving...` → guardando silenciosamente
- `Saved` → guardado (desaparece en 2 segundos)

### 2. Last Successful Run

Solo se actualiza cuando:

> Run → SQL válido → consulta ejecutada → gráficas generadas

Si hay error: **Last Successful Run NO cambia.**
El usuario no pierde absolutamente nada.

**Contenido guardado:**
SQL, resultado, schema, charts, layout, execution time, row count, timestamp.

### 3. Version History

Cada Run exitoso crea automáticamente una versión.
Sin botones de "Guardar versión" — ocurre solo.

**Panel lateral con historial:**

```
10:15 · 6 rows  · 2.3ms
09:42 · 12 rows · 4.1ms
```

**Acciones por versión:** Preview / Restore / Duplicate.

---

## Flujos

### Crear Dashboard

Click **"+ New Dashboard"**

- → `POST /dashboards` inmediato (UUID generado)
- → El dashboard YA existe en la DB
- → Abre editor con "Untitled Dashboard"
- → Cursor parpadeante en el nombre del header
- → Sin dialogs, sin wizards, sin interrupciones

### Cambiar nombre

Click en el título del header

- → Se convierte en input editable inline
- → `Enter` confirma
- → `Escape` cancela
- → Se guarda automáticamente

### Ejecutar

`Ctrl+Enter` o botón **Run**

- → Botón cambia a "Running..." con spinner
- → Botón "Cancel" siempre visible si tarda
- → La UI nunca se congela

### Run exitoso

> Running → Success → Charts aparecen

- → Last Successful Run actualizado
- → Version History +1
- → Todo automático, sin interrupciones

### Run con error

> Run → Error

- → Draft permanece intacto
- → Last Successful Run NO cambia
- → Version History NO cambia
- → El usuario no pierde nada

### Refresh del navegador

- → Carga el último dashboard activo
- → Recupera el Draft exacto
- → Muestra los últimos gráficos guardados
- → Aparece "Last run 5 min ago" + botón "Run Again"
- → NO re-ejecuta automáticamente por defecto

### Cambiar de Dashboard

- → Auto-save del Draft actual silencioso
- → Carga Draft del nuevo dashboard
- → Monaco muestra su SQL
- → Muestra últimos gráficos sin re-ejecutar

---

## Estados visuales

Solo en el header, **nunca** modals:

| Indicador     | Significado           |
| ------------- | --------------------- |
| `● Draft`     | cambios sin guardar   |
| `Saving...`   | guardando             |
| `Saved`       | guardado (desaparece) |
| `Running`     | ejecutando            |
| `Success`     | éxito (breve)         |
| `Error`       | error en el SQL       |

---

## Principios UX

1. Nunca preguntar para guardar
2. Nunca perder trabajo (Draft siempre guardado)
3. Nunca bloquear al usuario
4. El usuario siempre puede volver atrás (History)
5. El sistema debe ser invisible

---

## Versión de implementación

Este documento define el diseño completo. La implementación se divide en:

| Versión           | Alcance                                        |
| ----------------- | ---------------------------------------------- |
| **v0.2.8** (actual) | Draft auto-save + refresh funcional          |
| **v0.2.x**          | Last Successful Run separado del Draft        |
| **v0.2.x**          | Version History completo                      |
