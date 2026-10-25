# XSD, XSANDERS Design Kit

Auditoría de diseño de una aplicación entera, pantalla por pantalla, para
Claude Code. XSD se encarga de:

- la **ficha** del proyecto (cómo se levanta, cómo se entra, qué pantallas tiene);
- las **capturas** de cada pantalla, en escritorio y teléfono, y en cada variante de diseño;
- los **revisores** en paralelo, uno por grupo de pantallas;
- el **informe interactivo**, donde la persona decide cada mejora: *Aceptar*, *Dejar como está* u *Otro cambio*;
- el **plan** y su aplicación con agentes;
- la **segunda vuelta** sobre lo tocado.

Se pide con **«revisá el diseño de este proyecto con XSD»** o con `/xsd`.

## Instalar

En Claude Code:

```
/plugin marketplace add snavello/xsanders-design-kit
/plugin install xsd@xsanders-design-kit
```

Opcional, la ventana de avance del plan y de los agentes:

```
/plugin install avance-agentes@xsanders-design-kit
```

Para que todo el equipo lo tenga en un proyecto, en su `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "xsanders-design-kit": { "source": { "source": "github", "repo": "snavello/xsanders-design-kit" } }
  },
  "enabledPlugins": { "xsd@xsanders-design-kit": true }
}
```

Sin plugins: copiar `plugins/xsd/skills/xsd/` a `.claude/skills/xsd/` del
proyecto. La skill funciona igual, porque nombra todo relativo a su propia carpeta.

## Lo que necesita el proyecto

- **Una referencia de diseño.** Por defecto, la skill
  [Impeccable](https://github.com/pbakaus/impeccable) (Apache 2.0) en
  `.claude/skills/impeccable/`. Si el proyecto tiene reglas de diseño
  propias, se nombran en `lecturas` de la ficha: ante un choque, mandan esas.
- **Python 3 con Pillow**, para el informe y la hoja de contacto.
- **Node con Playwright y Chromium**, para las capturas. Si el navegador
  está en otro lugar: `XSD_CHROMIUM=/ruta/al/chromium`.
- **`xsd-trabajo/` en el `.gitignore`.** Ahí van las capturas, los
  hallazgos y el informe de cada corrida.

La primera vez, XSD arma `xsd/proyectos/<proyecto>/` en el repositorio: la
ficha, el inventario de pantallas, el script que firma las sesiones de cada
rol, el contexto y el historial. Pregunta solo lo que no puede deducir del código.

## El informe

Se publica como **artifact de claude.ai** con la capacidad `db`. Las
decisiones quedan en la base del propio informe, colección `decisiones`, y
Claude las lee de ahí. Sin claude.ai, el `index.html` local funciona igual:
guarda en el navegador y ofrece copiar las decisiones para pegarlas en la conversación.

## Qué hay acá

```
.claude-plugin/marketplace.json     el catálogo: xsd y avance-agentes
plugins/xsd/skills/xsd/
  SKILL.md                          cuándo y cómo la usa Claude
  METODO.md                         el método, fase por fase, y las lecciones
  plantillas/                       ficha.json y los tres encargos
  herramientas/xsd.py               capturar · hoja · brief · informe · decisiones · previos · encargos · avance
  herramientas/capturar.cjs         el capturador (Playwright)
  informe/index.html                la página del informe, sin librerías
plugins/avance-agentes/             mod de Claude Code: la ventana de avance
tests/                              python -m pytest -q tests
```

Primer uso: Colm3na, 2026-10-24/25. Fueron 61 pantallas, 8 revisores, 228
hallazgos y 144 decisiones en la primera vuelta, y todo se aplicó en cinco PR.
