#!/usr/bin/env python3
import json, os, re, shutil, tempfile, urllib.request, zipfile, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "VSB_Espanol_1.8.1.zip"

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8-sig"))

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def deep_strings(obj):
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, list):
        out=[]
        for x in obj: out.extend(deep_strings(x))
        return out
    if isinstance(obj, dict):
        out=[]
        for x in obj.values(): out.extend(deep_strings(x))
        return out
    return []

def translate_obj(obj, translator):
    if isinstance(obj, str):
        return translator(obj)
    if isinstance(obj, list):
        return [translate_obj(x, translator) for x in obj]
    if isinstance(obj, dict):
        return {k: translate_obj(v, translator) for k,v in obj.items()}
    return obj

# Manual high-confidence terms / fixes. These override automated output.
MANUAL = {
    "jaams_weaponry": {
        "item.jaams_weaponry.dynamite": "Dinamita",
        "tooltip.jaams_weaponry.throwable": "Arrojadizo",
        "tooltip.jaams_weaponry.throwable.desc": "Permite lanzar el objeto como proyectil.",
        "tooltip.jaams_weaponry.detonating": "Detonante",
        "tooltip.jaams_weaponry.detonating.desc": "Tiene una probabilidad de explotar y romperse al atacar.",
    },
    "sortilege": {
        "enchantment.sortilege.arcane": "Arcano",
        "enchantment.sortilege.arcane.desc": "Convierte el daño infligido en daño mágico.",
        "enchantment.sortilege.magic_protection": "Protección mágica",
        "enchantment.sortilege.magic_protection.desc": "Reduce el daño de fuentes mágicas.",
    },
    "infernalexp": {
        "enchantment.infernalexp.leaping": "Salto",
        "enchantment.infernalexp.leaping.desc": "Impulsa al portador hacia delante al usarlo en el aire o hace que rebote en el objetivo tras un golpe exitoso.",
    },
    "minecells": {
        "item.minecells.crowbar": "Palanca",
        "item.minecells.crowbar.description": "Inflige daño crítico después de romper una puerta.",
        "item.minecells.crit_damage": "Daño crítico: +%s HP",
    },
    "handcrafted": {
        "block.handcrafted.birch_couch": "Sofá de abedul",
        "tooltip.handcrafted.shift_description": "Mantén SHIFT para más información",
    },
    "apotheosis": {
        "text.apotheosis.when_socketed_in": "Al engarzarla en:",
        "gem_class.anything": "Cualquier objeto",
        "bonus.apotheosis:enchantment.desc.global": "+%s %s a todos los encantamientos existentes",
        "misc.apotheosis.level": "nivel",
        "misc.apotheosis.level.many": "niveles",
        "item.apotheosis.gem.apotheosis:the_end/endersurge": "Gema Endersurge",
        "text.apotheosis.unique": "Única",
        "text.apotheosis.socketable_into": "Encaja en:",
        "text.apotheosis.anything": "Cualquier objeto",
        "info.apotheosis.book_range": "Rango de poder: [%s, %s]",
        "info.apotheosis.discoverable": "Descubrible",
        "info.apotheosis.discoverable.not": "No descubrible",
        "info.apotheosis.lootable": "Obtenible como botín",
        "info.apotheosis.lootable.not": "No obtenible como botín",
        "info.apotheosis.tradeable": "Intercambiable",
        "info.apotheosis.tradeable.not": "No intercambiable",
        "info.apotheosis.treasure": "Tesoro",
        "info.apotheosis.treasure.not": "No es tesoro",
    },
    "summonerscrolls": {
        "item.summonerscrolls.charged_creeper_summoner_scroll": "Pergamino de invocación de Creeper cargado",
    },
    "abyssal_decor": {
        "block.abyssal_decor.scrimshaw_altar": "Altar de scrimshaw",
    },
}

# Keep these names stable instead of letting machine translation mutate them.
PROTECTED_TERMS = [
    "Vampires Strike Back","Vampirism","Dhampir","Ender","Netherite","Enderium",
    "Shinerite","Scrimshaw","Apotheosis","Mine Cells","Jaam's","KubeJS","Minecraft",
    "EMI","JEI","CurseForge","Shift","CTRL","Ctrl","WIP"
]
TOKEN_RE = re.compile(r"%(?:\d+\$)?[sdif]|§.|\\n|\n|https?://\S+|\[[^\]]+\]")

# Small post-translation glossary for Minecraft/mod terminology.
POST = [
    (r"\bdaño mágico\b", "daño mágico"),
    (r"\bmano principal\b", "mano principal"),
    (r"\benfriamiento\b", "enfriamiento"),
    (r"\bvelocidad de ataque\b", "velocidad de ataque"),
    (r"\bdaño de ataque\b", "daño de ataque"),
    (r"\balcance de entidades\b", "alcance de las entidades"),
    (r"\bprobabilidad crítica\b", "probabilidad de crítico"),
]

def install_argos():
    import argostranslate.package, argostranslate.translate
    installed = argostranslate.translate.get_installed_languages()
    en = next((x for x in installed if x.code == "en"), None)
    es = next((x for x in installed if x.code == "es"), None)
    if en and es and en.get_translation(es):
        return en.get_translation(es)
    argostranslate.package.update_package_index()
    pkgs = argostranslate.package.get_available_packages()
    pkg = next(p for p in pkgs if p.from_code == "en" and p.to_code == "es")
    path = pkg.download()
    argostranslate.package.install_from_path(path)
    installed = argostranslate.translate.get_installed_languages()
    en = next(x for x in installed if x.code == "en")
    es = next(x for x in installed if x.code == "es")
    return en.get_translation(es)

def make_translator():
    translation = install_argos()
    cache = {}
    def tx(text):
        if not text or not re.search(r"[A-Za-z]", text):
            return text
        if text in cache:
            return cache[text]
        # Protect formatting, placeholders and important proper nouns.
        protected = {}
        def stash(value):
            key = f" ZXQ{len(protected)}QXZ "
            protected[key.strip()] = value
            return key
        work = TOKEN_RE.sub(lambda m: stash(m.group(0)), text)
        for term in sorted(PROTECTED_TERMS, key=len, reverse=True):
            work = re.sub(re.escape(term), lambda m: stash(m.group(0)), work, flags=re.I)
        try:
            out = translation.translate(work)
        except Exception:
            out = text
        for key, val in protected.items():
            out = out.replace(key, val).replace(" "+key+" ", val)
        for pat, repl in POST:
            out = re.sub(pat, repl, out, flags=re.I)
        # Normalize common rarity/UI words that Argos sometimes varies.
        exact = {
            "Common":"Común","Uncommon":"Poco común","Rare":"Raro","Epic":"Épico",
            "Legendary":"Legendario","Unique":"Único","Damage":"Daño","Cooldown":"Enfriamiento",
            "Mana":"Maná","Level":"Nivel","Levels":"Niveles","Range":"Alcance",
            "Duration":"Duración","Throwable":"Arrojadizo","Detonating":"Detonante",
        }
        if text in exact: out = exact[text]
        cache[text] = out
        return out
    return tx

VSB_BASE = "https://raw.githubusercontent.com/VM-Chinese-translate-group/Vampires-Strike-Back-Chinese/main/Source/kubejs/assets"

# Full mod language sources for mods that visibly leaked English in-game.
FULL_SOURCES = {
    "irons_spellbooks": {
        "en": "https://raw.githubusercontent.com/iron431/irons-spells-n-spellbooks/1.20.1-legacy/src/main/resources/assets/irons_spellbooks/lang/en_us.json",
        "es": "https://raw.githubusercontent.com/iron431/irons-spells-n-spellbooks/1.20.1-legacy/src/main/resources/assets/irons_spellbooks/lang/es_es.json",
    },
    "minecells": {
        "en": "https://raw.githubusercontent.com/mim1q/MineCells/1.20.x/src/main/resources/assets/minecells/lang/en_us.json",
        "es": "https://raw.githubusercontent.com/mim1q/MineCells/1.20.x/src/main/resources/assets/minecells/lang/es_es.json",
    },
    "apotheosis": {
        "en": "https://raw.githubusercontent.com/Shadows-of-Fire/Apotheosis/1.20/src/main/resources/assets/apotheosis/lang/en_us.json",
        "es": "https://raw.githubusercontent.com/Shadows-of-Fire/Apotheosis/1.20/src/main/resources/assets/apotheosis/lang/es_es.json",
    },
    "handcrafted": {
        "en": "https://raw.githubusercontent.com/terrarium-earth/Handcrafted/8d21d1665916850c3fa3bdaf1370c50ec2ca7035/common/src/main/generated/resources/assets/handcrafted/lang/en_us.json",
        "es": "https://raw.githubusercontent.com/terrarium-earth/Handcrafted/8d21d1665916850c3fa3bdaf1370c50ec2ca7035/common/src/main/resources/assets/handcrafted/lang/es_mx.json",
    },
    "allurement": {
        "es": "https://raw.githubusercontent.com/team-abnormals/allurement/1.20.x/src/main/resources/assets/allurement/lang/es_es.json",
    },
}

def merge_missing(dst, src):
    for k,v in src.items():
        if k not in dst:
            dst[k] = v

def main():
    if not PACK.exists():
        raise SystemExit(f"Missing base pack: {PACK}")
    translator = make_translator()

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        work = td / "pack"
        with zipfile.ZipFile(PACK, "r") as z:
            z.extractall(work)

        # Preserve all hand-written/custom Spanish already present in the pack.
        existing = {}
        for p in work.glob("assets/*/lang/es_es.json"):
            try:
                existing[p.parts[-3]] = load_json(p)
            except Exception:
                pass

        # Discover every custom namespace provided by VSB's own source.
        tree_url = "https://api.github.com/repos/VM-Chinese-translate-group/Vampires-Strike-Back-Chinese/git/trees/main?recursive=1"
        with urllib.request.urlopen(tree_url, timeout=60) as r:
            tree = json.loads(r.read().decode("utf-8"))
        namespaces = sorted({
            p["path"].split("/")[3]
            for p in tree["tree"]
            if p["path"].startswith("Source/kubejs/assets/") and p["path"].endswith("/lang/en_us.json")
        })
        namespaces = sorted(set(namespaces) | set(FULL_SOURCES) | set(existing))

        report = {}
        for ns in namespaces:
            english = {}
            spanish = {}

            # Highest-quality official Spanish first when available.
            meta = FULL_SOURCES.get(ns, {})
            if meta.get("es"):
                try: spanish.update(fetch_json(meta["es"]))
                except Exception as e: print("WARN official ES", ns, e)
            if meta.get("en"):
                try: english.update(fetch_json(meta["en"]))
                except Exception as e: print("WARN official EN", ns, e)

            # VSB custom English strings (renames, pack-specific tooltips, etc.).
            try:
                pack_en = fetch_json(f"{VSB_BASE}/{ns}/lang/en_us.json")
                english.update(pack_en)
            except Exception:
                pass

            # Translate every English key that still lacks Spanish.
            translated = 0
            for k,v in english.items():
                if k not in spanish:
                    spanish[k] = translate_obj(v, translator)
                    translated += 1

            # Existing hand translations override everything above.
            if ns in existing:
                spanish.update(existing[ns])

            # High-confidence manual corrections override machine translation.
            spanish.update(MANUAL.get(ns, {}))

            if spanish:
                save_json(work / "assets" / ns / "lang" / "es_es.json", spanish)
                report[ns] = {
                    "english_keys_seen": len(english),
                    "spanish_keys_final": len(spanish),
                    "machine_filled": translated,
                    "manual_existing": len(existing.get(ns, {})),
                    "manual_fixes": len(MANUAL.get(ns, {})),
                }

        (work / "TRANSLATION_REPORT.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        # Refresh README inside resource pack.
        (work / "README.txt").write_text(
            "Vampires Strike Back 1.8.1 - Traduccion Espanol ES (V4 Global)\\n"
            "Minecraft 1.20.1\\n\\n"
            "Traduccion global ampliada por namespace/mod.\\n"
            "Incluye traducciones oficiales cuando existen, textos especificos de VSB\\n"
            "y traduccion automatica de claves faltantes, con correcciones manuales.\\n\\n"
            "Nota: textos escritos directamente en el codigo de un mod (hardcoded)\\n"
            "no pueden sustituirse mediante un resource pack normal.\\n",
            encoding="utf-8"
        )

        out = ROOT / "VSB_Espanol_1.8.1.new.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for p in sorted(work.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(work).as_posix())

        sha1 = hashlib.sha1(out.read_bytes()).hexdigest()
        shutil.move(out, PACK)
        (ROOT / "VSB_Espanol_1.8.1.sha1").write_text(sha1 + "\n", encoding="ascii")
        print("SHA1", sha1)
        print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
