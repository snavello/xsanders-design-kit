"""XSD, XSANDERS Design Kit: las piezas mecánicas funcionan con una corrida
armada a mano, sin navegador ni base de datos.

Se cuida lo que se rompería en silencio al usar el kit en otro proyecto: que
los manifiestos del plugin estén bien, que el encargo no deje marcadores sin
reemplazar, y que el informe, las decisiones, los antecedentes de la segunda
vuelta y los encargos del equipo salgan con el formato que espera la página.

Correr con: python -m pytest -q tests
"""
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
KIT = RAIZ / "plugins" / "xsd" / "skills" / "xsd"
sys.path.insert(0, str(KIT / "herramientas"))
import xsd  # noqa: E402


def test_los_manifiestos_apuntan_a_plugins_que_existen():
    mercado = json.loads((RAIZ / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    for p in mercado["plugins"]:
        manifiesto = json.loads((RAIZ / p["source"] / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        assert manifiesto["name"] == p["name"]


def test_la_skill_nombra_solo_rutas_del_kit():
    skill = (KIT / "SKILL.md").read_text(encoding="utf-8")
    assert skill.startswith("---\nname: xsd\n")
    for archivo in ("METODO.md", "herramientas/xsd.py", "plantillas/ficha.json", "informe/index.html"):
        assert (KIT / archivo).exists(), archivo
    assert "xsd/herramientas" not in skill and "xsd/plantillas" not in skill


def test_el_mod_lee_el_avance_del_proyecto():
    mod = RAIZ / "plugins" / "avance-agentes"
    assert "xsd-trabajo/avance.json" in (mod / "hooks" / "register.tsx").read_text(encoding="utf-8")


def test_el_informe_no_trae_nada_propio_de_un_proyecto():
    pagina = (KIT / "informe" / "index.html").read_text(encoding="utf-8")
    for palabra in ("Colm3na", "Bancaria", "PRUEBAS", "laguna", "noticiero"):
        assert palabra not in pagina, palabra
    assert pagina.startswith('<meta charset="utf-8">')


# --------------------------------------------------------- una corrida falsa
@pytest.fixture
def corrida(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pantallas.json").write_text(json.dumps([
        {"id": "app-inicio", "app": "App", "nombre": "Inicio", "url": "/", "rol": "ninguno", "temas": True},
        {"id": "app-datos", "app": "App", "nombre": "Datos", "url": "/datos", "rol": "ninguno", "temas": False},
    ]), encoding="utf-8")
    (tmp_path / "contexto.md").write_text("Una app de prueba.", encoding="utf-8")
    ficha = {"proyecto": "prueba", "nombre": "Prueba", "idioma": "castellano", "locale": "es-AR",
             "servidor": {"comando": "x", "puerto": 1}, "sesiones": {"comando": "x {variante} {quien}"},
             "roles": ["ninguno"], "variantes": {"con_variantes": ["claro"], "sin_variantes": "base"},
             "vistas": {"d": {"ancho": 1440, "alto": 900}, "m": {"ancho": 390, "alto": 844, "escala": 2}},
             "pantallas": "pantallas.json", "contexto": "contexto.md", "lecturas": ["REGLAS.md"],
             "referencia": ".claude/skills/impeccable", "trabajo": "trabajo",
             "aviso_capturas": "El distintivo no es diseño."}
    (tmp_path / "ficha.json").write_text(json.dumps(ficha), encoding="utf-8")
    c = tmp_path / "trabajo" / "c1"
    (c / "capturas").mkdir(parents=True)
    for nombre in ("claro-d-app-inicio", "claro-m-app-inicio", "base-d-app-datos"):
        Image.new("RGB", (1440 if "-d-" in nombre else 780, 1200), "white").save(c / "capturas" / f"{nombre}.png")
    (c / "grupos.json").write_text(json.dumps({"G1": {"titulo": "Todo", "pantallas": ["app-inicio", "app-datos"]}}),
                                   encoding="utf-8")
    (c / "hallazgos").mkdir()
    (c / "hallazgos" / "G1.json").write_text(json.dumps({"grupo": "G1", "pantallas": [
        {"id": "app-inicio", "resumen": "r", "nota": 7, "fortalezas": [], "hallazgos": [
            {"id": "G1-01", "titulo": "Baja", "severidad": "baja", "captura": "claro-d-app-inicio.png",
             "zona": {"x": 1, "y": 1, "w": 10, "h": 10}},
            {"id": "G1-02", "titulo": "Alta", "severidad": "alta", "captura": "claro-m-app-inicio.png",
             "zona": {"x": 1, "y": 1, "w": 0, "h": 10}}]},
        {"id": "general", "resumen": "g", "nota": None, "fortalezas": [], "hallazgos": [
            {"id": "G1-03", "titulo": "General", "severidad": "media", "captura": "base-d-app-datos.png"}]}],
        "verificacion": [{"id": "V-01", "resultado": "parcial", "comentario": "a medias"}]}), encoding="utf-8")
    return SimpleNamespace(ficha="ficha.json", corrida="c1", dir=c)


def _args(c, **extra):
    base = {"ficha": c.ficha, "corrida": c.corrida, "vuelta": 1, "titulo": None, "subtitulo": None, "intro": None}
    return SimpleNamespace(**{**base, **extra})


def test_el_encargo_no_deja_marcadores(corrida):
    xsd.brief(_args(corrida))
    texto = (corrida.dir / "brief.md").read_text(encoding="utf-8")
    assert not re.search(r"\{[A-Z_]+\}", texto)
    assert "Una app de prueba." in texto and "REGLAS.md" in texto


def test_el_informe_ordena_por_gravedad_y_limpia_las_zonas(corrida):
    xsd.informe(_args(corrida))
    datos = json.loads((corrida.dir / "informe" / "datos.json").read_text(encoding="utf-8"))
    inicio = next(p for p in datos["pantallas"] if p["id"] == "app-inicio")
    assert [h["id"] for h in inicio["hallazgos"]] == ["G1-02", "G1-01"]
    assert inicio["hallazgos"][0]["zona"] is None            # w = 0 no se dibuja
    assert inicio["hallazgos"][1]["capturaJpg"] == "claro-d-app-inicio.jpg"
    assert {c["modelo"] for c in inicio["capturas"]} == {"claro"}
    datos_p = next(p for p in datos["pantallas"] if p["id"] == "app-datos")
    assert [c["modelo"] for c in datos_p["capturas"]] == ["base"]
    assert any(p["id"] == "general-g1" for p in datos["pantallas"])
    assert datos["aviso_capturas"] == "El distintivo no es diseño."
    assert datos["clave"] == "xsd-prueba-c1"
    archivos = json.loads((corrida.dir / "informe" / "archivos.json").read_text(encoding="utf-8"))
    assert {"path": "datos.json"} in archivos and len(archivos) == 4
    assert (corrida.dir / "informe" / "index.html").exists()


def test_decisiones_previos_y_encargos(corrida, tmp_path):
    desde = tmp_path / "bajadas" / "decisiones"
    desde.mkdir(parents=True)
    (desde / "G1-01.json").write_text(json.dumps({"estado": "aceptar"}), encoding="utf-8")
    (desde / "G1-02.json").write_text(json.dumps({"estado": "cambio", "nota": "otra cosa"}), encoding="utf-8")
    (desde / "G1-03.json").write_text(json.dumps({"estado": "dejar"}), encoding="utf-8")
    xsd.decisiones(_args(corrida, desde=str(tmp_path / "bajadas")))
    cons = json.loads((corrida.dir / "consolidado.json").read_text(encoding="utf-8"))
    assert {h["id"]: h["estado"] for h in cons} == {"G1-01": "aceptar", "G1-02": "cambio", "G1-03": "dejar"}
    assert next(h for h in cons if h["id"] == "G1-02")["nota"] == "otra cosa"

    (corrida.dir / "aplicar.json").write_text(json.dumps({"equipo": {"hallazgos": ["G1-"], "parciales": ["V-01"]}}),
                                              encoding="utf-8")
    xsd.encargos(_args(corrida))
    enc = json.loads((corrida.dir / "encargos" / "equipo.json").read_text(encoding="utf-8"))
    assert [h["id"] for h in enc["hallazgos"]] == ["G1-01", "G1-02"]      # «dejar» no entra
    assert [p["id"] for p in enc["parciales_de_la_vuelta_anterior"]] == ["V-01"]

    xsd.previos(_args(corrida, consolidado=str(corrida.dir / "consolidado.json")))
    prev = json.loads((corrida.dir / "previos" / "G1.json").read_text(encoding="utf-8"))
    assert [p["id"] for p in prev["pantallas"]] == ["app-inicio", "app-datos"]
    # El general entra porque nombra una pantalla del grupo (en su captura), y
    # entra con su «dejar»: así el revisor sabe que no lo tiene que repetir.
    assert {h["id"]: h["estado"] for h in prev["hallazgos_anteriores"]} == {
        "G1-01": "aceptar", "G1-02": "cambio", "G1-03": "dejar"}


def test_el_avance_suma_y_actualiza_bloques(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    xsd.avance(SimpleNamespace(titulo="Plan", nota=None, bloque=["b1=en_curso:Capturas|empezando"]))
    xsd.avance(SimpleNamespace(titulo=None, nota="ok", bloque=["b1=hecho:", "b2=pendiente:Revisores"]))
    d = json.loads((tmp_path / "xsd-trabajo" / "avance.json").read_text(encoding="utf-8"))
    assert d["titulo"] == "Plan" and d["nota"] == "ok"
    assert [(b["id"], b["estado"], b["nombre"]) for b in d["bloques"]] == [("b1", "hecho", "Capturas"),
                                                                           ("b2", "pendiente", "Revisores")]
    assert d["bloques"][0]["detalle"] == "empezando"


# ------------------------------------------------------------------- catálogo
CATALOGO = KIT / "catalogo"
sys.path.insert(0, str(CATALOGO))
import armar  # noqa: E402


def _ids_del_catalogo():
    return [i for _, _, _, ids in armar.FAMILIAS for i in ids]


def test_cada_estilo_del_catalogo_tiene_su_hoja_y_su_ficha():
    ids = _ids_del_catalogo()
    assert len(ids) == len(set(ids)) == 60
    fichas = json.loads((CATALOGO / "estilos.json").read_text(encoding="utf-8"))
    for i in ids:
        css = (CATALOGO / "estilos" / f"{i}.css").read_text(encoding="utf-8")
        assert css.startswith("/* fuentes:"), i
        assert f".e-{i}" in css, i
        assert fichas[i]["nombre"] and fichas[i]["caracter"], i
        foto = re.search(r"/\*\s*foto:\s*([a-z]+)\s*(?:;\s*([a-z]+))?\s*\*/", css)
        for nombre in (foto.groups() if foto else ()):
            if nombre:
                assert (CATALOGO / "fotos" / f"{nombre}.jpg").exists(), (i, nombre)
    sobrantes = {p.name.split(".")[0] for p in (CATALOGO / "estilos").iterdir()} - set(ids)
    assert not sobrantes, sobrantes


def test_los_estilos_con_movimiento_respetan_reducir_movimiento():
    for fam, _, _, ids in armar.FAMILIAS:
        if fam.startswith("mov"):
            for i in ids:
                css = (CATALOGO / "estilos" / f"{i}.css").read_text(encoding="utf-8")
                assert "@keyframes" in css and "prefers-reduced-motion" in css, i


def test_las_fuentes_salen_en_un_solo_enlace_valido():
    fams = armar.unir_fuentes(armar.leer_fuentes("Barlow:wght@400;700; Barlow:wght@500; Manrope:wght@400..800; Manrope:wght@600"))
    assert fams == ["Barlow:wght@400;500;700", "Manrope:wght@400..800"]


def test_el_catalogo_se_arma(tmp_path):
    salida = tmp_path / "catalogo" / "index.html"
    sys.argv = ["armar.py", str(salida)]
    armar.main()
    pagina = salida.read_text(encoding="utf-8")
    assert pagina.count('<article class="est"') == 60
    assert "{{" not in pagina
    assert (salida.parent / "fotos" / "tecnico.jpg").exists()
