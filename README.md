# Minecraft Server Resources

Recursos públicos utilizados por los servidores privados de Minecraft.

## Vampires Strike Back — Español V4 Global

Resource pack de traducción al español para **Vampires Strike Back 1.8.1** en **Minecraft 1.20.1**.

La V4 amplía la traducción de forma global por mod/namespace: usa traducciones españolas oficiales cuando existen, conserva las traducciones específicas de Vampires Strike Back y completa claves faltantes de mods como **Iron's Spells 'n Spellbooks, Mine Cells, Handcrafted, Apotheosis, Jaam's Weaponry, Sortilege, Infernal Expansion, Summoner Scrolls, Abyssal Decor, Species, Odd Accessories, Unique Accessories** y otros recursos propios del modpack.

### Descarga directa

```text
https://raw.githubusercontent.com/ExoticSytem/minecraft-server-resources/main/VSB_Espanol_1.8.1.zip
```

### SHA-1 actual

```text
99ee68cdf26803fecab5590c369066ab72fbf371
```

### server.properties

```properties
resource-pack=https://raw.githubusercontent.com/ExoticSytem/minecraft-server-resources/main/VSB_Espanol_1.8.1.zip
resource-pack-sha1=99ee68cdf26803fecab5590c369066ab72fbf371
require-resource-pack=true
resource-pack-prompt={"text":"Este servidor utiliza la traducción al español de Vampires Strike Back.","color":"red"}
```

El archivo mantiene siempre la misma URL. Cuando cambia el contenido del ZIP, solo cambia el SHA-1 y ese valor debe actualizarse en `server.properties`.

La compilación global se genera mediante GitHub Actions y valida la integridad del ZIP antes de publicarlo.

> Algunos textos escritos directamente dentro del código de un mod (hardcoded) no pueden sustituirse mediante un resource pack normal.
