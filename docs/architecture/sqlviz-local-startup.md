# Arranque local y servicio Quack opcional

**Entregado:** 2026-10-06, en el árbol de trabajo; sin release ni commit nuevo.
**Alcance:** primera unidad de E0, correspondiente al arranque descrito en SEC-03.
No cierra la autorización de API ni el aislamiento analítico (SEC-01/02/04).

## Comportamiento

`sqlviz` y `sqlviz proyecto.sqlviz` escuchan por defecto en `127.0.0.1:4000`.
Demo y persistencia aplican la misma política de red. La opción `--host` permite
cambiarla explícitamente; las limitaciones de autorización del README siguen
vigentes, incluso si se configura una contraseña administrativa.

El arranque normal no carga ni instala Quack, ni inicia su puerto. Tener
`SQLVIZ_QUACK_TOKEN` en el entorno tampoco activa el servicio: hace falta `--quack`.

Con `--quack`:

- Se exige una credencial en `SQLVIZ_QUACK_TOKEN` de al menos 32 caracteres,
  descontando espacios de los extremos. Esta validación no demuestra entropía;
  generar un valor aleatorio y guardarlo como secreto.
- Se carga la extensión ya instalada y compatible con el DuckDB utilizado.
  SQLviz no descarga extensiones, no selecciona nightly ni actualiza Quack.
- El endpoint es `quack:127.0.0.1:9494`, incluso si el HTTP de SQLviz usa otro host.
- La credencial se transmite como parámetro enlazado y no se muestra en el banner
  ni en los mensajes de error de arranque de SQLviz.
- Una credencial inválida se rechaza antes de crear/abrir el proyecto. Un fallo
  de carga o inicio termina el CLI con código 1; no continúa silenciosamente.
- Al salir, se solicita detener Quack antes de cerrar la conexión del proyecto.

Quack es acceso directo a la base y utiliza una credencial distinta del login o
enlace compartido. No es el canal utilizado por los viewers HTTP y no aplica sus
permisos. En esta etapa sigue exponiendo la base de proyecto a quien posea esa
credencial; su aislamiento está fuera del alcance de esta unidad.

## Configuración opcional

Preparar la extensión por separado, con la misma versión de DuckDB que utilizará
SQLviz. El repositorio estable es `core`; no usar la instalación nightly de los
ejemplos históricos. La instalación manual requiere una decisión del operador,
no forma parte del arranque.

Ejemplo PowerShell para un entorno local de prueba con la extensión instalada:

```powershell
$env:SQLVIZ_QUACK_TOKEN = uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
uv run sqlviz --quack --no-browser
Remove-Item Env:SQLVIZ_QUACK_TOKEN
```

La credencial dura lo que dure ese entorno; no se persiste en el proyecto.
No incluirla en argumentos, archivos versionados o capturas de consola.

La documentación oficial describe
[inicio, instalación y autenticación](https://github.com/duckdb/duckdb-quack) y
[las funciones de inicio y parada](https://duckdb.org/docs/current/quack/reference).
Esas referencias definen Quack; la política más restrictiva de este documento
define su uso dentro de SQLviz.

## Responsabilidades y recursos

| Componente | Responsabilidad |
| --- | --- |
| `cli.py` | Argumentos, opt-in, lectura de credencial, creación/apertura y cierre de la conexión del proyecto |
| `server.py` | Ensamblar FastAPI/uvicorn y liberar recursos derivados aunque falle el arranque |
| `quack.py` | Validar credencial, iniciar y detener el servicio opcional; traducir errores sin revelar SQL/parámetros |

`serve()` recibe una conexión prestada: no la cierra. El CLI es su propietario.
`ExitStack` libera el cursor derivado y la sesión Quack cuando falla la creación
de la aplicación, la configuración del servidor o su ejecución. Si no se puede
crear el cursor requerido, el arranque falla en lugar de usar un fallback implícito.
Un cursor sigue siendo acceso al mismo DuckDB escribible, no aislamiento de lectura.

## Evidencia de cierre

- **28 pruebas nuevas** de CLI/servidor: defaults en demo/proyecto nuevo/existente,
  opt-in, credencial ausente/inválida, configuración LAN explícita, parámetros
  enlazados, errores sin credenciales y limpieza con fallos parciales/interrupciones.
- Suite Python completa: **1419 pasan, 3 omitidas**, en 131,10 s. Comando local:
  `.venv/Scripts/python.exe -m pytest --tb=short -q --basetemp build/startup-review/pytest-full-01`.
  Esa carpeta se creó expresamente para esta ejecución; pytest puede eliminar
  el contenido de `--basetemp` al reutilizarla. No apuntar a carpetas con datos.
- `ruff` correcto y `mypy` correcto sobre los seis archivos de código del CLI.
  El chequeo global mantiene los dos errores previos de inference/API.
- Ensayo real en Windows con el CLI y uvicorn, puerto HTTP efímero y demo en memoria:
  `/api/v1/auth/me` devuelve 200/demo y `Get-NetTCPConnection` observa exactamente
  un listener propio, en `127.0.0.1`. Cierre controlado sin tocar la demo del usuario.
- Ensayo real de Quack previamente instalado, DuckDB 1.5.4: parámetros enlazados
  aceptados, listener local iniciado y puerto cerrado al salir del contexto.

Las pruebas automatizadas no descargan Quack ni abren puertos. Los ensayos reales
son validación adicional del entorno local, no certificación de otras plataformas.
En Windows se usó una carpeta temporal dentro de `build/startup-review/`, porque
el directorio temporal por defecto de pytest no permitía acceso.

**Continuación entregada:** [autorización por recurso y solicitud](sqlviz-authorization.md)
y [ejecución analítica aislada](sqlviz-analytical-execution.md), conservando los
flujos legítimos de compartir. Este documento conserva la evidencia del arranque.
