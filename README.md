# Minecraft Server Resources

Recursos públicos utilizados por los servidores privados de Minecraft.

## Vampires Strike Back — Español

Resource pack de traducción al español para **Vampires Strike Back 1.8.1** en **Minecraft 1.20.1**.

### Descarga directa

```text
https://raw.githubusercontent.com/ExoticSytem/minecraft-server-resources/main/VSB_Espanol_1.8.1.zip
```

### SHA-1

```text
42bd08912b48c8be436cc049491f09784ee66987
```

### server.properties

```properties
resource-pack=https://raw.githubusercontent.com/ExoticSytem/minecraft-server-resources/main/VSB_Espanol_1.8.1.zip
resource-pack-sha1=42bd08912b48c8be436cc049491f09784ee66987
require-resource-pack=true
resource-pack-prompt={"text":"Este servidor utiliza la traducción al español de Vampires Strike Back.","color":"red"}
```

El ZIP se reconstruye automáticamente mediante GitHub Actions desde los archivos de `source/` y el workflow comprueba el SHA-1 antes de publicarlo.

> Si se modifica el resource pack, hay que actualizar también el SHA-1 configurado en `server.properties`.
