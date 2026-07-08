<div align="center">

# Lnk2SymLnk

**Converts Windows `.lnk` shortcut files into Linux symbolic links**  
Clean dark PyQt6 GUI · Bilingual EN/PT-BR · CLI fallback · Dry-run mode

[🇧🇷 Português Brasileiro](#lnk2symlnk-pt-br)

</div>

---

## How it works

Windows stores shortcuts as binary `.lnk` files that Linux simply ignores.
Lnk2SymLnk reads each file, extracts the target path, maps the Windows drive
letter to its Linux mount point, and creates a native symlink in place of the
`.lnk` file — so your file manager, shell, and every other tool on Linux can
follow them normally.

---

## Features

| | |
|---|---|
| 🔍 Auto-scan | Scanning begins as soon as you pick a folder — no extra button |
| 📁 Recursive | Finds `.lnk` files buried in any depth of sub-folders |
| 🧪 Dry-run | Preview every symlink that *would* be created, nothing written to disk |
| 🗺️ Drive mapping | Map any number of Windows drive letters (`X:`, `Y:`, `Z:`, UNC…) to Linux paths |
| 📄 Single file | Browse and convert one `.lnk` directly instead of a whole folder |
| 📝 Activity log | Timestamped, color-coded output for every action (Log tab) |
| 🎨 Theme-aware | Follows your system light/dark preference; Catppuccin Mocha palette in dark mode |
| 🌐 Bilingual | EN-US / PT-BR toggle, remembered across sessions |
| 🖥️ Menu integration | Desktop entry, app-menu launcher, and `.lnk` MIME association after install |
| ⌨️ CLI mode | `--no-gui` flag for scripting and headless use |

---

## Requirements

- Python 3.10+
- PyQt6 (`pip install PyQt6`)
- pylnk3 (`pip install pylnk3`) — installed automatically on first run

GTK3 bindings are **not** required; the GUI is pure PyQt6.

---

## Quick Start

### Run without Installing

```bash
python3 lnk2symlink.py
```

Dependencies (`PyQt6`, `pylnk3`) are fetched automatically on the first run if
they are not already present.

### Build & Install (system-wide)

```bash
chmod +x build.sh && ./build.sh
```

Run as your normal user — **not** with `sudo`. The script asks for your password
only for the two steps that actually need root: copying files into `/opt/` and
placing the launcher in `/usr/local/bin/`. Everything else (desktop entry, icon,
MIME registration) lands in `~/.local/share/`, scoped to your account.

If you do run `sudo ./build.sh`, it detects the real user via `$SUDO_USER` and
still writes those files to your home directory, not root's.

**After install, the build creates:**

| Path | Purpose |
|---|---|
| `/opt/wsl-symlink/` | Program files |
| `/usr/local/bin/wsl-symlink` | Launcher in `$PATH` |
| `~/.local/share/applications/Lnk2SymLnk.desktop` | App menu entry (KDE, GNOME, …) |
| `~/.local/share/icons/lnk2symlnk.svg` | Icon |
| `lnk2symlnk_config_linux.ini` | Settings (created next to the script on first run) |

The build finishes with a self-check that confirms the files landed and the
Python source is syntactically valid before declaring success.

---

## CLI Usage

```
python3 lnk2symlink.py --no-gui [DIR]
  --dry-run / -n       Preview only, no symlinks created
  --mount LETTER:PATH  Map a drive letter, e.g. -m X:/mnt/disk1
  --no-recurse         Scan top-level folder only
  --lang pt            Portuguese output
  --help               All options
```

---

## Settings File

Settings are saved next to the script as `lnk2symlnk_config_linux.ini`
(or `_windows.ini` on Windows), so the program is fully portable — move
the folder and your preferences travel with it.

```ini
[main]
last_folder = /mnt/sda1/Users/Casa/Links
lang = en
recursive = true

[drive_map]
x = /mnt/Disco_Local1
y = /run/media/x/Seagate1
z = /mnt/Disco_Local
```

If a legacy `.json` config exists from an older version it is read
automatically and migrated to `.ini` on the next save.

---

## Project Layout

```
lnk2symlink.py              Main script (GUI + CLI in one file)
build.sh                    Builds the launcher and installs desktop integration
Lnk2SymLnk                 Generated launcher (created by build.sh)
lnk2symlnk_config_linux.ini Settings (created on first run)
```

---

## License and Credits

GNU AGPLv3

Made by **Ium101**

---
---

<div align="center">

# Lnk2SymLnk <a name="lnk2symlnk-pt-br"></a>

**Converte arquivos de atalho `.lnk` do Windows em links simbólicos do Linux**  
Interface escura em PyQt6 · Bilíngue EN/PT-BR · Modo CLI · Simulação (dry-run)

[🇺🇸 English](#lnk2symlnk)

</div>

---

## Como funciona

O Windows armazena atalhos como arquivos binários `.lnk` que o Linux simplesmente ignora.
O Lnk2SymLnk lê cada arquivo, extrai o caminho de destino, mapeia a letra de unidade
do Windows para seu ponto de montagem no Linux e cria um link simbólico nativo no lugar
do arquivo `.lnk` — para que seu gerenciador de arquivos, terminal e qualquer outra
ferramenta no Linux possam seguí-los normalmente.

---

## Funcionalidades

| | |
|---|---|
| 🔍 Varredura automática | A varredura começa assim que você escolhe uma pasta — sem botão extra |
| 📁 Recursivo | Encontra arquivos `.lnk` em qualquer nível de subpastas |
| 🧪 Simulação | Pré-visualize cada link simbólico que *seria* criado, sem gravar nada em disco |
| 🗺️ Mapeamento de unidades | Mapeie qualquer número de letras de unidade do Windows (`X:`, `Y:`, `Z:`, UNC…) para caminhos Linux |
| 📄 Arquivo único | Navegue e converta um `.lnk` diretamente em vez de uma pasta inteira |
| 📝 Log de atividades | Saída com carimbo de data/hora e código de cores para cada ação (aba Log) |
| 🎨 Tema adaptável | Segue a preferência do sistema (claro/escuro); paleta Catppuccin Mocha no modo escuro |
| 🌐 Bilíngue | Alternância EN-US / PT-BR, memorizada entre sessões |
| 🖥️ Integração ao menu | Entrada `.desktop`, launcher no menu de aplicativos e associação MIME para `.lnk` após instalação |
| ⌨️ Modo CLI | Flag `--no-gui` para scripts e uso sem interface gráfica |

---

## Requisitos

- Python 3.10+
- PyQt6 (`pip install PyQt6`)
- pylnk3 (`pip install pylnk3`) — instalado automaticamente na primeira execução

As ligações GTK3 **não** são necessárias; a interface é puramente PyQt6.

---

## Início Rápido

### Executar sem Instalar

```bash
python3 lnk2symlink.py
```

As dependências (`PyQt6`, `pylnk3`) são obtidas automaticamente na primeira execução,
caso ainda não estejam presentes.

### Build e Instalação (sistema)

```bash
chmod +x build.sh && ./build.sh
```

Execute como seu usuário normal — **não** com `sudo`. O script pede sua senha apenas
nas duas etapas que realmente precisam de root: copiar arquivos para `/opt/` e colocar
o launcher em `/usr/local/bin/`. Todo o resto (entrada `.desktop`, ícone, registro MIME)
vai para `~/.local/share/`, vinculado à sua conta.

Se você executar `sudo ./build.sh`, o script detecta o usuário real via `$SUDO_USER` e
ainda assim grava esses arquivos no seu diretório home, não no do root.

**Após a instalação, o build cria:**

| Caminho | Finalidade |
|---|---|
| `/opt/wsl-symlink/` | Arquivos do programa |
| `/usr/local/bin/wsl-symlink` | Launcher no `$PATH` |
| `~/.local/share/applications/Lnk2SymLnk.desktop` | Entrada no menu de aplicativos (KDE, GNOME, …) |
| `~/.local/share/icons/lnk2symlnk.svg` | Ícone |
| `lnk2symlnk_config_linux.ini` | Configurações (criado ao lado do script na primeira execução) |

O build termina com uma verificação automática que confirma que os arquivos foram criados
corretamente e que o código Python é sintaticamente válido, antes de declarar sucesso.

---

## Uso pela CLI

```
python3 lnk2symlink.py --no-gui [DIR]
  --dry-run / -n       Apenas pré-visualização, nenhum link simbólico criado
  --mount LETRA:CAMINHO  Mapeia uma letra de unidade, ex.: -m X:/mnt/disco1
  --no-recurse         Varre apenas a pasta raiz, sem subpastas
  --lang pt            Saída em português
  --help               Todas as opções
```

---

## Arquivo de Configurações

As configurações são salvas ao lado do script como `lnk2symlnk_config_linux.ini`
(ou `_windows.ini` no Windows), tornando o programa totalmente portátil — mova
a pasta e suas preferências vão junto.

```ini
[main]
last_folder = /mnt/sda1/Users/Casa/Links
lang = pt
recursive = true

[drive_map]
x = /mnt/Disco_Local1
y = /run/media/x/Seagate1
z = /mnt/Disco_Local
```

Se existir um arquivo de configuração legado em `.json` de uma versão anterior,
ele é lido automaticamente e migrado para `.ini` no próximo salvamento.

---

## Estrutura do Projeto

```
lnk2symlink.py              Script principal (GUI + CLI em um único arquivo)
build.sh                    Constrói o launcher e instala a integração ao desktop
Lnk2SymLnk                 Launcher gerado (criado pelo build.sh)
lnk2symlnk_config_linux.ini Configurações (criado na primeira execução)
```

---

## Licença e Créditos

GNU AGPLv3

Feito por **Ium101**
