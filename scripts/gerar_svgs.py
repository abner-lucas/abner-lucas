#!/usr/bin/env python3
"""
Gera as imagens animadas do README com a identidade visual de profabnerlucas.com:
cores e fontes do portfólio, robozinho mascote, etiquetas com porca sextavada e
trilha de circuito, faixa de tecnologias e cartões dos subapps.

Uso:
    pip install fonttools
    python scripts/gerar_svgs.py

Imagens no GitHub não carregam recursos externos, então as fontes do site
(Bricolage Grotesque, Manrope, JetBrains Mono e Caveat) são baixadas do Google
Fonts só com os caracteres usados e embutidas em cada SVG. As capas dos subapps
vêm de abner-lucas/portfolio (public/midia/projetos).
"""
import base64
import hashlib
import io
import json
import random
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

from fontTools.ttLib import TTFont

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / 'assets'
CACHE = Path(__file__).resolve().parent / '.cache'
USUARIO = 'abner-lucas'
PORTFOLIO = f'https://raw.githubusercontent.com/{USUARIO}/portfolio/main'

# --------------------------------------------------------------------------
# Tokens (os mesmos de app/globals.css do portfólio)
# --------------------------------------------------------------------------

PALCO = '#0b1f19'
PALCO_2 = '#0d241d'
PALCO_CARTAO = '#10291f'
PALCO_BORDA = '#1f3d33'
PALCO_TINTA = '#eaf3ee'
PALCO_SUAVE = '#a4bcb1'
TINTA_ESCURA = '#0c1a15'
LIMA = '#c8f05a'
CORAL = '#ff6b4a'
VERDE = '#22b07d'
MARCA = '#0e7a54'

TEMAS = {
    'claro': {'tinta': '#0c1a15', 'suave': '#4a5b53', 'marca': '#0e7a54', 'superficie': '#ffffff'},
    'escuro': {'tinta': '#e6efea', 'suave': '#9db1a7', 'marca': '#3dd69b', 'superficie': '#0e1714'},
}
TONS = {
    'verde': '#22b07d', 'lima': '#c8f05a', 'coral': '#ff6b4a',
    'violeta': '#7c5cff', 'ambar': '#f5b83d', 'azul': '#3a8dff',
}

FONTES = {
    'display': ('Bricolage Grotesque', 800),
    'titulo': ('Bricolage Grotesque', 700),
    'texto': ('Manrope', 500),
    'forte': ('Manrope', 700),
    'mono': ('JetBrains Mono', 500),
    'mono-forte': ('JetBrains Mono', 700),
    'mao': ('Caveat', 700),
}
EMOJI = "'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji'"
UA_NAVEGADOR = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
)
EASE = 'cubic-bezier(.16,1,.3,1)'

# Ícones do Lucide (ISC), a mesma biblioteca usada no site.
ICONES = {
    'cerebro': '<path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M9 13a4.5 4.5 0 0 0 3-4"/><path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/><path d="M3.477 10.896a4 4 0 0 1 .585-.396"/><path d="M6 18a4 4 0 0 1-1.967-.516"/><path d="M12 13h4"/><path d="M12 18h6a2 2 0 0 1 2 2v1"/><path d="M12 8h8"/><path d="M16 8V5a2 2 0 0 1 2-2"/><circle cx="16" cy="13" r=".5"/><circle cx="18" cy="3" r=".5"/><circle cx="20" cy="21" r=".5"/><circle cx="20" cy="8" r=".5"/>',
    'robo': '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>',
    'local': '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    'engrenagem': '<path d="M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z"/><path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"/><path d="M12 2v2"/><path d="M12 22v-2"/><path d="m17 20.66-1-1.73"/><path d="M11 10.27 7 3.34"/><path d="m20.66 17-1.73-1"/><path d="m3.34 7 1.73 1"/><path d="M14 12h8"/><path d="M2 12h2"/><path d="m20.66 7-1.73 1"/><path d="m3.34 17 1.73-1"/><path d="m17 3.34-1 1.73"/><path d="m11 13.73-4 6.93"/>',
    'seta': '<path d="M7 7h10v10"/><path d="M7 17 17 7"/>',
    'linkedin': '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/>',
    'capelo': '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>',
    'email': '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
}

# --------------------------------------------------------------------------
# Conteúdo (espelha conteudo/perfil.ts e conteudo/subapps.ts do portfólio)
# --------------------------------------------------------------------------

SUBAPPS = [
    {
        'capa': 'missao-osi', 'nome': 'Missão OSI · Investigadores da Rede', 'categoria': 'Redes de Computadores',
        'descricao': 'A rede do laboratório caiu! Estudantes investigam as sete camadas com testes simulados, Atlas OSI e caderno de evidências.',
        'tecnologias': ['Next.js', 'Simulação', 'Gamificação'], 'repositorio': 'missao-osi', 'tom': 'verde',
    },
    {
        'capa': 'geo3d', 'nome': 'Geo3D · Laboratório Interativo', 'categoria': 'Computação Gráfica',
        'descricao': 'Cinco sólidos com animações de planificação, projeções ortogonais e dez desafios. Acessível (WCAG 2.2 AA) e com Libras.',
        'tecnologias': ['Three.js', 'Next.js', 'Supabase'], 'repositorio': 'geo3d-lab-interativo-cg', 'tom': 'lima',
    },
    {
        'capa': 'letramento-ia', 'nome': 'Letramento Digital em IA', 'categoria': 'Extensão',
        'descricao': 'Curso de Letramento Digital em IA para estudantes e comunidades de Belém, em parceria PRODEPA, iSACI, IFPA e UFPA.',
        'tecnologias': ['Next.js', 'Engenharia de prompts', 'IA'], 'repositorio': 'letramento-digital-em-ia', 'tom': 'violeta',
    },
    {
        'capa': 'monitor-acai', 'nome': 'MonitorAçaí', 'categoria': 'Pesquisa · IoT',
        'descricao': 'Rodízio aleatório de sensores de umidade do solo (FDR) no sistema agroflorestal irrigado de açaí do Campus Breves.',
        'tecnologias': ['Next.js', 'Supabase', 'SheetJS'], 'repositorio': 'monitor-acai', 'tom': 'coral',
    },
    {
        'capa': 'computacao-grafica', 'nome': 'Portal de Computação Gráfica', 'categoria': 'Disciplina',
        'descricao': 'Trilha de aprendizado, modelos 3D interativos com Three.js e roteiros das avaliações práticas da disciplina.',
        'tecnologias': ['Three.js', 'WebGL', 'GLTF'], 'repositorio': 'computacao-grafica', 'tom': 'azul',
    },
    {
        'capa': 'programacao-web', 'nome': 'Portal de Programação Web', 'categoria': 'Disciplina',
        'descricao': 'Projetos práticos comentados, roteiros em PDF e pacotes de atividades de HTML5, CSS3 e JavaScript.',
        'tecnologias': ['HTML5', 'CSS3', 'JavaScript'], 'repositorio': 'programacao-web', 'tom': 'ambar',
    },
]

TITULOS = [
    {'arquivo': '01-sobre', 'numero': 1, 'rotulo': 'Sobre mim', 'titulo': 'Prazer, eu sou', 'destaque': 'Ábner Lucas.'},
    {'arquivo': '02-laboratorio', 'numero': 2, 'rotulo': 'Laboratório aberto', 'titulo': 'Subapps que viram',
     'destaque': 'sala de aula.', 'nota': 'psiu: tudo é código aberto, pode estudar à vontade!'},
    {'arquivo': '03-pesquisa', 'numero': 3, 'rotulo': 'Pesquisa & produção', 'titulo': 'Ciência feita',
     'destaque': 'no Marajó.', 'nota': 'do açaí às ondas cerebrais'},
    {'arquivo': '04-github', 'numero': 4, 'rotulo': 'No GitHub', 'titulo': 'Código em',
     'destaque': 'movimento.', 'nota': 'commits, estrelas e uma cobrinha faminta'},
]

FAIXA = [
    'Robótica', 'Three.js', 'Sensores', 'Deep Learning', 'RoboCup Junior', 'Next.js', 'Python', 'MNE-Python',
    'WebGL', 'Redes Neurais', 'IoT', 'Tinkercad', 'Blender', 'Supabase', 'Git & GitHub',
]

# --------------------------------------------------------------------------
# Download com cache, fontes e medidas de texto
# --------------------------------------------------------------------------


def baixar(url, ua='gerar-svgs'):
    CACHE.mkdir(parents=True, exist_ok=True)
    arquivo = CACHE / hashlib.sha1(f'{url}|{ua}'.encode()).hexdigest()
    if arquivo.exists():
        return arquivo.read_bytes()
    pedido = urllib.request.Request(url, headers={'User-Agent': ua})
    dados = urllib.request.urlopen(pedido, timeout=60).read()
    arquivo.write_bytes(dados)
    return dados


def url_fonte(chave, texto=None, woff2=False):
    familia, peso = FONTES[chave]
    consulta = {'family': f'{familia}:wght@{peso}'}
    if texto:
        consulta['text'] = texto
    css = baixar('https://fonts.googleapis.com/css2?' + urllib.parse.urlencode(consulta),
                 UA_NAVEGADOR if woff2 else 'gerar-svgs').decode()
    return re.search(r'url\((\S+?)\)', css).group(1)


class Metrica:
    def __init__(self, dados):
        fonte = TTFont(io.BytesIO(dados))
        self.cmap = fonte.getBestCmap()
        self.avancos = fonte['hmtx'].metrics
        self.upm = fonte['head'].unitsPerEm

    def largura(self, texto, tamanho, espacamento=0):
        total = sum(self.avancos[self.cmap[ord(c)]][0] if ord(c) in self.cmap else self.upm * 1.15 for c in texto)
        return total * tamanho / self.upm + espacamento * max(len(texto) - 1, 0)


_metricas = {}


def metrica(chave):
    if chave not in _metricas:
        _metricas[chave] = Metrica(baixar(url_fonte(chave)))
    return _metricas[chave]


def largura(chave, texto, tamanho, espacamento=0):
    return metrica(chave).largura(texto, tamanho, espacamento)


def quebrar(chave, texto, tamanho, maximo):
    linhas, atual = [], ''
    for palavra in texto.split():
        tentativa = f'{atual} {palavra}'.strip()
        if atual and largura(chave, tentativa, tamanho) > maximo:
            linhas.append(atual)
            atual = palavra
        else:
            atual = tentativa
    return linhas + [atual]


def font_face(chave, caracteres):
    m = metrica(chave)
    texto = ''.join(sorted({c for c in caracteres if ord(c) in m.cmap} | {' '}))
    dados = baixar(url_fonte(chave, texto, woff2=True), UA_NAVEGADOR)
    b64 = base64.b64encode(dados).decode()
    return f"@font-face{{font-family:'{chave}';font-weight:{FONTES[chave][1]};src:url(data:font/woff2;base64,{b64}) format('woff2')}}"


def esc(texto):
    return texto.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def n(valor):
    return f'{valor:.1f}'.rstrip('0').rstrip('.')


# --------------------------------------------------------------------------
# Montagem de SVG
# --------------------------------------------------------------------------

CSS_BASE = (
    f'.sobe{{animation:sobe 1.1s {EASE} backwards}}'
    '@keyframes sobe{from{transform:translateY(var(--d,80px))}}'
    f'.surge{{animation:surge 1s {EASE} backwards}}'
    '@keyframes surge{from{opacity:0;transform:translateY(24px)}}'
    '.flutua{animation:flutua 5s ease-in-out infinite}'
    '@keyframes flutua{50%{transform:translateY(-9px)}}'
    '.gira{transform-box:fill-box;transform-origin:center;animation:gira 40s linear infinite}'
    '@keyframes gira{to{transform:rotate(360deg)}}'
    '.gira-rapido{transform-box:fill-box;transform-origin:center;animation:gira 8s linear infinite}'
    '.pulsa{animation:pulsa 2s ease-in-out infinite}'
    '@keyframes pulsa{50%{opacity:.45}}'
    '.cursor{animation:cursor 1s steps(1) infinite}'
    '@keyframes cursor{50%{opacity:0}}'
    '.robo-led{animation:robo-led 1.4s ease-in-out infinite}'
    '@keyframes robo-led{50%{opacity:.35}}'
    '.robo-olhos{transform-box:fill-box;transform-origin:center;animation:robo-piscar 4.5s infinite}'
    '@keyframes robo-piscar{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}'
    '.robo-braco{transform-box:view-box;transform-origin:63px 70px;animation:robo-acenar 2.2s ease-in-out infinite}'
    '@keyframes robo-acenar{0%,60%,100%{transform:rotate(0)}70%{transform:rotate(-22deg)}80%{transform:rotate(8deg)}90%{transform:rotate(-16deg)}}'
    '.risca{animation:risca .9s ease-in-out backwards}'
    '@keyframes risca{from{stroke-dashoffset:1}}'
    '.digita{transform-box:fill-box;transform-origin:0 50%}'
    '@keyframes digita{from{transform:scaleX(0)}}'
    f'.aperta{{transform-box:fill-box;transform-origin:center;animation:aperta .9s {EASE} backwards}}'
    '@keyframes aperta{from{opacity:0;transform:rotate(-150deg) scale(.4)}}'
    '.estoura{transform-box:fill-box;transform-origin:center;animation:estoura .5s cubic-bezier(.34,1.56,.64,1) backwards}'
    '@keyframes estoura{from{transform:scale(0)}}'
    '@media (prefers-reduced-motion:reduce){*{animation:none!important}}'
)


class Svg:
    def __init__(self, largura, altura, rotulo):
        self.largura, self.altura, self.rotulo = largura, altura, rotulo
        self.defs, self.corpo, self.css = [], [], []
        self.usos = defaultdict(set)
        self._ids = 0

    def id(self, prefixo):
        self._ids += 1
        return f'{prefixo}{self._ids}'

    def texto(self, x, y, conteudo, fonte, tamanho, cor, *, espacamento=0, ancora=None, classe='', estilo='', extra=''):
        self.usos[fonte].update(conteudo)
        classes = f'f-{fonte} {classe}'.strip()
        attrs = [f'x="{n(x)}"', f'y="{n(y)}"', f'font-size="{n(tamanho)}"', f'fill="{cor}"', f'class="{classes}"']
        if espacamento:
            attrs.append(f'letter-spacing="{n(espacamento)}"')
        if ancora:
            attrs.append(f'text-anchor="{ancora}"')
        if estilo:
            attrs.append(f'style="{estilo}"')
        if extra:
            attrs.append(extra)
        return f'<text {" ".join(attrs)}>{esc(conteudo)}</text>'

    def tspans(self, x, y, partes, fonte, tamanho, *, espacamento=0, classe='', estilo=''):
        """Uma linha com trechos de cores diferentes: partes = [(texto, cor), ...]."""
        for conteudo, _ in partes:
            self.usos[fonte].update(conteudo)
        miolo = ''.join(f'<tspan fill="{cor}">{esc(t)}</tspan>' for t, cor in partes)
        ls = f' letter-spacing="{n(espacamento)}"' if espacamento else ''
        st = f' style="{estilo}"' if estilo else ''
        return f'<text x="{n(x)}" y="{n(y)}" font-size="{n(tamanho)}" class="f-{fonte} {classe}"{ls}{st} xml:space="preserve">{miolo}</text>'

    def svg(self):
        faces = ''.join(font_face(k, v) for k, v in sorted(self.usos.items()))
        classes = ''.join(
            f".f-{k}{{font-family:'{k}',{EMOJI},sans-serif;font-weight:{FONTES[k][1]}}}" for k in sorted(self.usos)
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(self.largura)} {n(self.altura)}" '
            f'width="{n(self.largura)}" height="{n(self.altura)}" role="img" aria-label="{esc(self.rotulo)}">'
            f'<title>{esc(self.rotulo)}</title><style>{faces}{classes}{CSS_BASE}{"".join(self.css)}</style>'
            f'<defs>{"".join(self.defs)}</defs>{"".join(self.corpo)}</svg>'
        )


def icone(nome, x, y, tamanho, cor, espessura=2):
    escala = tamanho / 24
    return (
        f'<g transform="translate({n(x)} {n(y)}) scale({n(escala)})" fill="none" stroke="{cor}" '
        f'stroke-width="{espessura}" stroke-linecap="round" stroke-linejoin="round">{ICONES[nome]}</g>'
    )


def robozinho(x, y, largura, corpo=LIMA, tinta=TINTA_ESCURA, halo=None):
    """Mascote de componentes/ui/Robotica.tsx: LED pisca, olhos piscam e o braço acena."""
    def contorno(cor, extra):
        return (
            f'<g stroke="{cor}" fill="{cor}" stroke-width="{3.5 + extra}">'
            f'<path d="M45 16V6"/><circle cx="45" cy="6" r="4.5"/>'
            f'<rect x="9" y="30" width="7" height="14" rx="3"/><rect x="74" y="30" width="7" height="14" rx="3"/>'
            f'<rect x="16" y="16" width="58" height="42" rx="12"/><rect x="27" y="62" width="36" height="26" rx="7"/>'
            f'<path d="M27 70 16 80"/><g class="robo-braco"><path d="M63 70 75 58"/><circle cx="77" cy="55" r="4.5"/></g></g>'
        )

    altura = largura * 96 / 90
    miolo = contorno(halo, 6) if halo else ''
    miolo += (
        f'<path d="M45 16V6" stroke="{tinta}" stroke-width="3.5"/>'
        f'<circle cx="45" cy="6" r="4.5" fill="{CORAL}" stroke="{tinta}" stroke-width="2.5" class="robo-led"/>'
        f'<rect x="9" y="30" width="7" height="14" rx="3" fill="{corpo}" stroke="{tinta}" stroke-width="3"/>'
        f'<rect x="74" y="30" width="7" height="14" rx="3" fill="{corpo}" stroke="{tinta}" stroke-width="3"/>'
        f'<rect x="16" y="16" width="58" height="42" rx="12" fill="{corpo}" stroke="{tinta}" stroke-width="3.5"/>'
        f'<g class="robo-olhos"><circle cx="34" cy="35" r="5.5" fill="{tinta}"/><circle cx="56" cy="35" r="5.5" fill="{tinta}"/></g>'
        f'<path d="M36 47q9 6 18 0" stroke="{tinta}" stroke-width="3"/>'
        f'<rect x="27" y="62" width="36" height="26" rx="7" fill="{corpo}" stroke="{tinta}" stroke-width="3.5"/>'
        f'<circle cx="45" cy="75" r="4" fill="{tinta}"/>'
        f'<path d="M27 70 16 80" stroke="{tinta}" stroke-width="3.5"/>'
        f'<g class="robo-braco"><path d="M63 70 75 58" stroke="{tinta}" stroke-width="3.5"/>'
        f'<circle cx="77" cy="55" r="4.5" fill="{corpo}" stroke="{tinta}" stroke-width="3"/></g>'
    )
    return (
        f'<svg x="{n(x)}" y="{n(y)}" width="{n(largura)}" height="{n(altura)}" viewBox="0 0 90 96" overflow="visible" '
        f'fill="none" stroke-linecap="round" stroke-linejoin="round">{miolo}</svg>'
    )


def grao(s, largura, altura, raio):
    fid = s.id('grao')
    s.defs.append(
        f'<filter id="{fid}" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" '
        f'baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>'
    )
    return f'<rect width="{largura}" height="{altura}" rx="{raio}" filter="url(#{fid})" opacity=".07" style="mix-blend-mode:overlay"/>'


def campo_neural(s, largura, altura, semente=7, pontos=46, alcance=135):
    """Versão estática de CampoNeural.tsx: nós conectados com sinais percorrendo as ligações."""
    rnd = random.Random(semente)
    nos = [(rnd.uniform(10, largura - 10), rnd.uniform(10, altura - 10)) for _ in range(pontos)]
    ligacoes = []
    for i, (x1, y1) in enumerate(nos):
        for j in range(i + 1, len(nos)):
            x2, y2 = nos[j]
            if (x1 - x2) ** 2 + (y1 - y2) ** 2 < alcance ** 2:
                ligacoes.append((i, j))
    partes = [f'<g stroke="{PALCO_SUAVE}" stroke-opacity=".13" stroke-width="1">']
    partes += [f'<path d="M{n(nos[i][0])} {n(nos[i][1])}L{n(nos[j][0])} {n(nos[j][1])}"/>' for i, j in ligacoes]
    partes.append(f'</g><g fill="{PALCO_SUAVE}">')
    for k, (x, y) in enumerate(nos):
        atraso = rnd.uniform(0, 3)
        classe = ' class="pulsa"' if k % 3 == 0 else ''
        partes.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rnd.uniform(1.4, 2.6))}" opacity=".55"{classe} style="animation-delay:{n(atraso)}s"/>')
    partes.append('</g>')
    for i, j in rnd.sample(ligacoes, min(7, len(ligacoes))):
        (x1, y1), (x2, y2) = nos[i], nos[j]
        dur = rnd.uniform(2.4, 4.2)
        inicio = rnd.uniform(0, 3)
        partes.append(
            f'<circle r="2.4" fill="{LIMA}" opacity="0"><animateMotion dur="{n(dur)}s" begin="{n(inicio)}s" '
            f'repeatCount="indefinite" path="M{n(x1)} {n(y1)}L{n(x2)} {n(y2)}"/>'
            f'<animate attributeName="opacity" values="0;.9;.9;0" dur="{n(dur)}s" begin="{n(inicio)}s" repeatCount="indefinite"/></circle>'
        )
    return ''.join(partes)


def pilula(s, x, y, rotulo, icone_nome, cor_icone, atraso, duracao):
    """Etiqueta flutuante da abertura (IA & redes neurais, Robótica & sensores...)."""
    tam = 14.5
    w = 18 + 18 + 9 + largura('forte', rotulo, tam) + 18
    h = 40
    return (
        f'<g class="surge" style="animation-delay:{atraso}s"><g class="flutua" style="animation-duration:{duracao}s;animation-delay:{atraso}s">'
        f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{h}" rx="20" fill="{PALCO}" fill-opacity=".92" stroke="{PALCO_BORDA}"/>'
        + icone(icone_nome, x + 18, y + 11, 18, cor_icone)
        + s.texto(x + 18 + 18 + 9, y + 25.5, rotulo, 'forte', tam, PALCO_TINTA)
        + '</g></g>'
    ), w


# --------------------------------------------------------------------------
# Peças
# --------------------------------------------------------------------------


def abertura(numeros):
    L, A, R = 1000, 588, 28
    s = Svg(L, A, 'Olá, eu sou o Ábner! Tecnologia que se aprende fazendo. Professor EBTT do IFPA Campus Breves, no Marajó.')
    clip = s.id('palco')
    s.defs.append(f'<clipPath id="{clip}"><rect width="{L}" height="{A}" rx="{R}"/></clipPath>')
    s.defs.append(
        '<radialGradient id="brilho-lima"><stop offset="0" stop-color="#c8f05a" stop-opacity=".2"/>'
        '<stop offset=".65" stop-color="#c8f05a" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="brilho-verde"><stop offset="0" stop-color="#22b07d" stop-opacity=".24"/>'
        '<stop offset=".65" stop-color="#22b07d" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="anel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{LIMA}"/>'
        f'<stop offset=".5" stop-color="{VERDE}"/><stop offset="1" stop-color="{MARCA}"/></linearGradient>'
        f'<radialGradient id="miolo"><stop offset="0" stop-color="#14352a"/><stop offset="1" stop-color="{PALCO_2}"/></radialGradient>'
    )
    c = s.corpo
    c.append(f'<g clip-path="url(#{clip})"><rect width="{L}" height="{A}" fill="{PALCO}"/>')
    c.append('<circle cx="930" cy="20" r="420" fill="url(#brilho-lima)"/><circle cx="60" cy="600" r="420" fill="url(#brilho-verde)"/>')
    c.append(campo_neural(s, L, A))
    c.append(grao(s, L, A, R))

    # Texto da esquerda
    x0 = 56
    ola = 'Olá, eu sou o Ábner!'
    w_ola = largura('mao', ola, 32)
    c.append(f'<g class="surge" style="animation-delay:.15s">{s.texto(x0, 92, ola, "mao", 32, LIMA)}'
             f'<svg x="{n(x0 + w_ola + 12)}" y="66" width="54" height="27" viewBox="0 0 60 30"><path d="M2 6c14 2 30 6 40 18m0 0-9-1m9 1 1-9" '
             f'fill="none" stroke="{LIMA}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></g>')
    c.append(s.tspans(x0, 130, [('SENTIR ', PALCO_SUAVE), ('→', LIMA), (' PENSAR ', PALCO_SUAVE), ('→', LIMA), (' AGIR', PALCO_SUAVE)],
                      'mono', 12.5, espacamento=3.75, classe='surge', estilo='animation-delay:.25s'))

    tam, entre = 66, 63
    linhas = [('Tecnologia que', PALCO_TINTA), ('se aprende', PALCO_TINTA), ('fazendo.', LIMA)]
    for i, (linha, cor) in enumerate(linhas):
        base = 208 + i * entre
        cid = s.id('linha')
        s.defs.append(f'<clipPath id="{cid}"><rect x="{x0 - 6}" y="{base - tam}" width="600" height="{tam + 18}"/></clipPath>')
        c.append(f'<g clip-path="url(#{cid})">'
                 + s.texto(x0, base, linha, 'display', tam, cor, espacamento=-1.3, classe='sobe',
                           estilo=f'--d:{tam + 12}px;animation-delay:{n(.35 + i * .1)}s') + '</g>')
    w_faz = largura('display', 'fazendo.', tam, -1.3)
    y_risco = 208 + 2 * entre + 6
    c.append(f'<svg x="{x0}" y="{y_risco}" width="{n(w_faz)}" height="16" viewBox="0 0 300 20" preserveAspectRatio="none" overflow="visible">'
             f'<path d="M3 14C60 4 140 2 297 9" fill="none" stroke="{LIMA}" stroke-width="6" stroke-linecap="round" '
             f'vector-effect="non-scaling-stroke" pathLength="1" stroke-dasharray="1" class="risca" style="animation-delay:1.25s"/></svg>')
    chamada = ['Professor EBTT do IFPA Campus Breves, no Marajó.',
               'Disciplinas, laboratórios interativos e pesquisas em',
               'Inteligência Computacional e Robótica.']
    c.append('<g class="surge" style="animation-delay:.75s">'
             + ''.join(s.texto(x0, 396 + i * 25, t, 'texto', 17, PALCO_SUAVE) for i, t in enumerate(chamada)) + '</g>')

    # Retrato do robozinho com anel, balão e etiquetas
    cx, cy = 772, 252
    c.append(f'<g class="surge" style="animation-delay:.3s">'
             f'<circle cx="{cx}" cy="{cy}" r="186" fill="none" stroke="{LIMA}" stroke-opacity=".45" stroke-width="1.5" stroke-dasharray="4 10" class="gira"/>'
             f'<circle cx="{cx}" cy="{cy}" r="160" fill="url(#miolo)" stroke="url(#anel)" stroke-width="8"/>'
             + robozinho(cx - 95, cy - 112, 190, halo=PALCO_TINTA) + '</g>')
    balao = ('<path d="M20 0H192A20 20 0 0 1 212 20V58A20 20 0 0 1 192 78H8A6 6 0 0 1 2 72V20A20 20 0 0 1 20 0Z" '
             f'fill="{LIMA}"/>')
    c.append(f'<g transform="translate(548 52) rotate(-6)"><g class="estoura" style="animation-delay:1.1s">'
             f'<g class="flutua" style="animation-duration:6s">{balao}'
             + s.texto(22, 33, 'bora criar algo', 'mao', 25, TINTA_ESCURA)
             + s.texto(22, 62, 'incrível? ✨', 'mao', 25, TINTA_ESCURA) + '</g></g></g>')
    p1, w1 = pilula(s, 0, 0, 'IA & redes neurais', 'cerebro', LIMA, 1.3, 5)
    c.append(f'<g transform="translate({n(976 - w1)} 112)">{p1}</g>')
    p2, _ = pilula(s, 0, 0, 'Robótica & sensores', 'robo', LIMA, 1.45, 6)
    c.append(f'<g transform="translate(560 356)">{p2}</g>')
    p3, w3 = pilula(s, 0, 0, 'IFPA Campus Breves', 'local', CORAL, 1.6, 5.5)
    c.append(f'<g transform="translate({n(930 - w3)} 418)">{p3}</g>')

    # Números
    c.append(f'<path d="M{x0} 486H{L - x0}" stroke="{PALCO_BORDA}"/>')
    col = (L - 2 * x0) / len(numeros)
    for i, (valor, rotulo) in enumerate(numeros):
        x = x0 + i * col
        c.append(f'<g class="surge" style="animation-delay:{n(.9 + i * .1)}s">'
                 + s.texto(x, 536, valor, 'titulo', 38, PALCO_TINTA)
                 + s.texto(x, 559, rotulo, 'texto', 13.5, PALCO_SUAVE) + '</g>')
    c.append('</g>')
    return s.svg()


def titulo_secao(dados, tema):
    t = TEMAS[tema]
    L = 1000
    tam = 46
    A = 168
    rotulo = dados['rotulo'].upper()
    s = Svg(L, A, f"{dados['numero']:02d} · {dados['rotulo']}: {dados['titulo']} {dados['destaque']}")
    c = s.corpo

    # Etiqueta: porca sextavada + trilha de circuito + rótulo digitado com cursor
    c.append(f'<svg x="0" y="0" width="36" height="36" viewBox="0 0 36 36" overflow="visible"><g class="aperta">'
             f'<path d="M18 2.5 31.4 10.25V25.75L18 33.5 4.6 25.75V10.25Z" fill="{t["superficie"]}" stroke="{t["marca"]}" stroke-width="2" stroke-linejoin="round"/>'
             f'<circle cx="18" cy="18" r="10" fill="none" stroke="{t["marca"]}" stroke-opacity=".3" stroke-width="1.5"/></g>'
             + s.texto(18, 22, f"{dados['numero']:02d}", 'mono-forte', 11, t['marca'], ancora='middle', classe='surge',
                       estilo='animation-delay:.3s') + '</svg>')
    c.append(f'<svg x="40" y="10" width="64" height="16" viewBox="0 0 64 16" overflow="visible" fill="none" stroke="{t["marca"]}" '
             f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
             f'<path d="M0 8H16L22 2H40L46 8H56" pathLength="1" stroke-dasharray="1" class="risca" style="animation-duration:.45s;animation-delay:.15s"/>'
             f'<circle cx="59.5" cy="8" r="3.5" class="estoura" style="animation-delay:.55s"/></svg>')
    esp = 2.4
    x_rot = 112
    w_rot = largura('mono', rotulo, 12, esp)
    cid = s.id('digita')
    s.defs.append(f'<clipPath id="{cid}"><rect x="{x_rot - 2}" y="6" width="{n(w_rot + 6)}" height="24" class="digita" '
                  f'style="animation:digita .5s steps({len(rotulo)}) .5s backwards"/></clipPath>')
    c.append(f'<g clip-path="url(#{cid})">' + s.texto(x_rot, 22.5, rotulo, 'mono', 12, t['marca'], espacamento=esp) + '</g>')
    c.append(f'<rect x="{n(x_rot + w_rot + 6)}" y="11" width="7.5" height="14" fill="{t["marca"]}" class="cursor"/>')

    # Título com as palavras subindo uma a uma
    indice = 0
    larguras = []
    for linha, (texto, cor) in enumerate([(dados['titulo'], t['tinta']), (dados['destaque'], t['marca'])]):
        base = 98 + linha * 52
        cid = s.id('linha')
        s.defs.append(f'<clipPath id="{cid}"><rect x="-4" y="{base - tam}" width="{L}" height="{tam + 14}"/></clipPath>')
        x = 0
        partes = []
        for palavra in texto.split(' '):
            partes.append(s.texto(x, base, palavra, 'titulo', tam, cor, espacamento=-0.9, classe='sobe',
                                  estilo=f'--d:{tam + 10}px;animation-delay:{n(.1 + indice * .05)}s'))
            x += largura('titulo', palavra + ' ', tam, -0.9)
            indice += 1
        larguras.append(x)
        c.append(f'<g clip-path="url(#{cid})">{"".join(partes)}</g>')

    if dados.get('nota'):
        tam_nota = 25
        w_nota = largura('mao', dados['nota'], tam_nota)
        if L - w_nota < larguras[1] + 40:
            raise SystemExit(f"Nota longa demais para o título {dados['arquivo']}")
        c.append(f'<g transform="translate({L - 6} 142) rotate(-3)"><g class="surge" style="animation-delay:.8s">'
                 + s.texto(0, 0, dados['nota'], 'mao', tam_nota, t['marca'], ancora='end') + '</g></g>')
    return s.svg()


def faixa(tema):
    t = TEMAS[tema]
    tam, h, pad = 40, 92, 26
    itens = []
    x = 0
    for i, item in enumerate(FAIXA):
        w = largura('titulo', item, tam, -0.6)
        itens.append((x + pad, item, i % 2 == 1))
        x += pad + w + pad
        itens.append((x, None, None))
        x += 30
    total = x
    s = Svg(1000, h, 'Tecnologias: ' + ', '.join(FAIXA))
    mid = s.id('borda')
    s.defs.append(
        f'<linearGradient id="{mid}g"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".09" stop-color="#fff"/>'
        f'<stop offset=".91" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<mask id="{mid}"><rect width="1000" height="{h}" fill="url(#{mid}g)"/></mask>'
    )
    duracao = total / 38
    s.css.append(f'.trilho{{animation:trilho {n(duracao)}s linear infinite}}@keyframes trilho{{to{{transform:translateX(-{n(total)}px)}}}}')
    partes = []
    for copia in (0, total):
        for xi, item, contorno in itens:
            if item is None:
                partes.append(f'<g transform="translate({n(copia + xi)} {h / 2 - 14})"><g class="gira-rapido">'
                              + icone('engrenagem', 0, 0, 28, t['marca']) + '</g></g>')
            elif contorno:
                partes.append(s.texto(copia + xi, h / 2 + 14, item, 'titulo', tam, 'none', espacamento=-0.6,
                                      extra=f'stroke="{t["suave"]}" stroke-width="1.4"'))
            else:
                partes.append(s.texto(copia + xi, h / 2 + 14, item, 'titulo', tam, t['tinta'], espacamento=-0.6))
    s.corpo.append(f'<g mask="url(#{mid})"><g class="trilho">{"".join(partes)}</g></g>')
    return s.svg()


def capa(nome):
    bruto = baixar(f'{PORTFOLIO}/public/midia/projetos/{nome}.svg').decode()
    raiz = re.search(r'<svg([^>]*)>', bruto)
    attrs = re.sub(r'\s(xmlns|viewBox|width|height)="[^"]*"', '', raiz.group(1))
    miolo = bruto[raiz.end():bruto.rindex('</svg>')]
    return attrs, miolo


def cartoes():
    L, R, pad = 480, 28, 26
    w_texto = L - 2 * pad
    medidas = []
    for app in SUBAPPS:
        titulo = quebrar('titulo', app['nome'], 23, w_texto)
        descricao = quebrar('texto', app['descricao'], 15, w_texto)
        medidas.append((titulo, descricao))
    max_t = max(len(m[0]) for m in medidas)
    max_d = max(len(m[1]) for m in medidas)
    A = 300 + pad + max_t * 29 + 12 + max_d * 23 + 18 + 26 + 20 + 42 + 16 + 14 + pad

    arquivos = {}
    for app, (titulo, descricao) in zip(SUBAPPS, medidas):
        tom = TONS[app['tom']]
        s = Svg(L, A, f"{app['nome']} ({app['categoria']}): {app['descricao']}")
        clip, clip_capa = s.id('cartao'), s.id('capa')
        s.defs.append(f'<clipPath id="{clip}"><rect width="{L}" height="{A}" rx="{R}"/></clipPath>'
                      f'<clipPath id="{clip_capa}"><rect width="{L}" height="300"/></clipPath>')
        attrs, miolo = capa(app['capa'])
        c = s.corpo
        c.append(f'<g clip-path="url(#{clip})"><rect width="{L}" height="{A}" fill="{PALCO_CARTAO}"/>')
        c.append(f'<g clip-path="url(#{clip_capa})"><rect width="{L}" height="300" fill="{tom}"/>'
                 f'<svg x="0" y="0" width="{L}" height="300" viewBox="0 0 800 500" preserveAspectRatio="xMidYMid slice"{attrs}>{miolo}</svg></g>')
        w_cat = largura('forte', app['categoria'], 12.5) + 26
        c.append(f'<rect x="16" y="16" width="{n(w_cat)}" height="28" rx="14" fill="{TINTA_ESCURA}" fill-opacity=".82"/>'
                 + s.texto(29, 34.5, app['categoria'], 'forte', 12.5, '#ffffff'))
        y = 300 + pad + 22
        for linha in titulo:
            c.append(s.texto(pad, y, linha, 'titulo', 23, PALCO_TINTA, espacamento=-0.3))
            y += 29
        y += 12 - 29 + 23
        for linha in descricao:
            c.append(s.texto(pad, y, linha, 'texto', 15, PALCO_SUAVE))
            y += 23
        y = 300 + pad + max_t * 29 + 12 + max_d * 23 + 18
        x = pad
        for tec in app['tecnologias']:
            w = largura('mono', tec, 12) + 22
            c.append(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="26" rx="13" fill="{PALCO}"/>'
                     + s.texto(x + 11, y + 17.5, tec, 'mono', 12, PALCO_SUAVE))
            x += w + 7
        y += 26 + 20
        rotulo = 'Abrir o subapp'
        w_bt = 20 + largura('forte', rotulo, 14.5) + 10 + 16 + 20
        c.append(f'<rect x="{pad}" y="{n(y)}" width="{n(w_bt)}" height="42" rx="21" fill="{tom}"/>'
                 + s.texto(pad + 20, y + 26.5, rotulo, 'forte', 14.5, TINTA_ESCURA)
                 + icone('seta', pad + w_bt - 36, y + 13, 16, TINTA_ESCURA, 2.4))
        y += 42 + 16 + 11
        c.append(s.texto(pad, y, f"código aberto · github.com/{USUARIO}/{app['repositorio']}", 'mono', 11.5, PALCO_SUAVE))
        c.append(f'</g><rect x=".75" y=".75" width="{L - 1.5}" height="{n(A - 1.5)}" rx="{R}" fill="none" stroke="{PALCO_BORDA}" stroke-width="1.5"/>')
        arquivos[app['capa']] = s.svg()
    return arquivos


def sobre(retrato):
    L, A = 440, 540
    s = Svg(L, A, 'Foco, curiosidade e código. Professor desde 2015.')
    cx0, cy0, cw, ch, cr = 30, 24, 380, 478, 32
    clip, clip_foto = s.id('cartao'), s.id('foto')
    r = cw * 0.78 / 2
    fx, fy = cx0 + cw + 24 - r, cy0 + ch + 24 - r
    s.defs.append(f'<clipPath id="{clip}"><rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="{cr}"/></clipPath>'
                  f'<clipPath id="{clip_foto}"><circle cx="{n(fx)}" cy="{n(fy)}" r="{n(r - 3)}"/></clipPath>')
    c = s.corpo
    c.append(f'<g transform="rotate(-2 {L / 2} {A / 2})"><g clip-path="url(#{clip})">'
             f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" fill="{LIMA}"/>')
    c.append(f'<g transform="translate({cx0 + 28} {cy0 + 70}) rotate(-3)">'
             + ''.join(s.texto(0, i * 46, t, 'mao', 50, TINTA_ESCURA) for i, t in enumerate(['foco,', 'curiosidade', '& código.']))
             + '</g>')
    lado = 2 * r * 1.13
    c.append(f'<g clip-path="url(#{clip_foto})"><rect x="{n(fx - r)}" y="{n(fy - r)}" width="{n(2 * r)}" height="{n(2 * r)}" fill="{PALCO}"/>'
             f'<image href="{retrato}" x="{n(fx - lado / 2)}" y="{n(fy - lado / 2)}" width="{n(lado)}" height="{n(lado)}" preserveAspectRatio="xMidYMid slice"/></g>'
             f'<circle cx="{n(fx)}" cy="{n(fy)}" r="{n(r - 3)}" fill="none" stroke="{TINTA_ESCURA}" stroke-width="6"/>')
    c.append(f'<g transform="rotate(6 {cx0 + cw - 62} {cy0 + 70})">' + robozinho(cx0 + cw - 110, cy0 + 26, 92, corpo='#ffffff') + '</g>')
    c.append('</g></g>')
    rotulo = 'professor desde 2015 ✦'
    w = largura('mao', rotulo, 27) + 34
    c.append(f'<g transform="translate(4 404) rotate(-8)"><g class="flutua" style="animation-duration:6s">'
             f'<rect width="{n(w)}" height="50" rx="16" fill="{PALCO}"/>'
             + s.texto(17, 33, rotulo, 'mao', 27, LIMA) + '</g></g>')
    return s.svg()


def botao(rotulo, fundo, cor, nome_icone=None, cor_icone=None, borda=None, seta=False, orcid=False):
    tam, h = 15.5, 46
    w = 20
    if nome_icone or orcid:
        w += 18 + 9
    w_txt = largura('forte', rotulo, tam)
    w += w_txt + (10 + 30 + 8 if seta else 20)
    s = Svg(w, h, rotulo)
    st = f' stroke="{borda}" stroke-width="1.5"' if borda else ''
    s.corpo.append(f'<rect x=".75" y=".75" width="{n(w - 1.5)}" height="{h - 1.5}" rx="{n((h - 1.5) / 2)}" fill="{fundo}"{st}/>')
    x = 20
    if nome_icone:
        s.corpo.append(icone(nome_icone, x, 14, 18, cor_icone or cor))
        x += 27
    elif orcid:
        s.corpo.append(f'<circle cx="{x + 9}" cy="23" r="9" fill="{cor_icone}"/>'
                       + s.texto(x + 9, 26.5, 'iD', 'mono-forte', 9.5, TINTA_ESCURA, ancora='middle'))
        x += 27
    s.corpo.append(s.texto(x, 28.5, rotulo, 'forte', tam, cor))
    if seta:
        cx = x + w_txt + 10 + 15
        s.corpo.append(f'<circle cx="{n(cx)}" cy="23" r="15" fill="{TINTA_ESCURA}" fill-opacity=".1"/>'
                       + icone('seta', cx - 8, 15, 16, cor, 2.4))
    return s.svg()


def rodape():
    L, A, R = 1000, 210, 28
    s = Svg(L, A, 'ábner.lucas · sentir. pensar. agir.')
    clip = s.id('palco')
    s.defs.append(f'<clipPath id="{clip}"><rect width="{L}" height="{A}" rx="{R}"/></clipPath>'
                  '<radialGradient id="brilho-r"><stop offset="0" stop-color="#c8f05a" stop-opacity=".16"/>'
                  '<stop offset=".65" stop-color="#c8f05a" stop-opacity="0"/></radialGradient>')
    c = s.corpo
    c.append(f'<g clip-path="url(#{clip})"><rect width="{L}" height="{A}" fill="{PALCO}"/>'
             f'<circle cx="960" cy="0" r="320" fill="url(#brilho-r)"/>')
    c.append(campo_neural(s, L, A, semente=11, pontos=20, alcance=150))
    c.append(grao(s, L, A, R))
    x0, tam = 48, 42
    w1 = largura('display', 'ábner', tam, -0.8)
    w2 = largura('display', '.', tam, -0.8)
    c.append(s.texto(x0, 84, 'ábner', 'display', tam, PALCO_TINTA, espacamento=-0.8)
             + s.texto(x0 + w1, 84, '.', 'display', tam, LIMA, classe='pulsa')
             + s.texto(x0 + w1 + w2, 84, 'lucas', 'display', tam, PALCO_TINTA, espacamento=-0.8))
    c.append(s.texto(x0, 114, 'Professor EBTT · Eixo Informação e Comunicação · IFPA Campus Breves', 'texto', 14.5, PALCO_SUAVE))
    c.append(robozinho(L - 48 - 84, 26, 84, halo=PALCO_TINTA))
    c.append(f'<g transform="translate({L - 48 - 84 - 22} 84) rotate(-3)">'
             + s.texto(0, 0, 'sentir. pensar. agir.', 'mao', 32, LIMA, ancora='end') + '</g>')
    c.append(f'<path d="M{x0} 146H{L - x0}" stroke="{PALCO_BORDA}"/>')
    c.append(s.texto(x0, 182, 'Prof. Me. Ábner Lucas · Breves, Marajó (PA)', 'texto', 13.5, PALCO_SUAVE))
    c.append(s.texto(L - x0, 182, 'profabnerlucas.com', 'mono', 13, LIMA, ancora='end'))
    c.append('</g>')
    return s.svg()


# --------------------------------------------------------------------------


def gravar(caminho, conteudo):
    destino = SAIDA / caminho
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(conteudo, encoding='utf-8')
    print(f'{caminho}: {len(conteudo.encode()) / 1024:.0f} KB')


def main():
    from datetime import date

    repos = json.loads(baixar(f'https://api.github.com/users/{USUARIO}'))['public_repos']
    numeros = [
        (str(date.today().year - 2015), 'anos de docência (desde 2015)'),
        ('69', 'turmas no SIGAA'),
        (str(repos), 'repositórios abertos'),
        (str(len(SUBAPPS)), 'subapps educacionais'),
    ]
    gravar('abertura.svg', abertura(numeros))
    for dados in TITULOS:
        for tema in TEMAS:
            gravar(f"titulos/{dados['arquivo']}-{tema}.svg", titulo_secao(dados, tema))
    for tema in TEMAS:
        gravar(f'faixa-{tema}.svg', faixa(tema))
    for nome, conteudo in cartoes().items():
        gravar(f'subapps/{nome}.svg', conteudo)
    foto = baixar(f'https://avatars.githubusercontent.com/{USUARIO}?s=460')
    tipo = 'image/png' if foto[:4] == b'\x89PNG' else 'image/jpeg'
    gravar('sobre.svg', sobre(f'data:{tipo};base64,{base64.b64encode(foto).decode()}'))
    gravar('botoes/fale-comigo.svg', botao('Fale comigo', MARCA, '#ffffff', 'email'))
    gravar('botoes/site.svg', botao('profabnerlucas.com', LIMA, TINTA_ESCURA, seta=True))
    gravar('botoes/linkedin.svg', botao('LinkedIn', PALCO, PALCO_TINTA, 'linkedin', LIMA, borda='#2b5446'))
    gravar('botoes/lattes.svg', botao('Lattes', PALCO, PALCO_TINTA, 'capelo', LIMA, borda='#2b5446'))
    gravar('botoes/orcid.svg', botao('ORCID', PALCO, PALCO_TINTA, cor_icone=LIMA, borda='#2b5446', orcid=True))
    gravar('rodape.svg', rodape())


if __name__ == '__main__':
    main()
