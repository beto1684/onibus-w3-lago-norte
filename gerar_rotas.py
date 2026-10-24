"""Gera rotas.js com as linhas de ônibus que passam pela W3 Norte e pela EPPN
em frente à SHIN QI 6 (Lago Norte), a partir do GeoServer público da Semob-DF.

Critério, usando só dados e nomenclatura oficiais da Semob:
  1. o itinerário passa a até 35 m de uma das paradas da SHIN QI 6 na EPPN
     (2293 "SHIN APOS ENTRADA DA QI/QL 06 EPPN" e 2294 "SHIN QI 6 EPPN");
     esse filtro espacial roda no próprio GeoServer (DWITHIN), sem baixar
     as ~1400 rotas do DF;
  2. o itinerário passa a até 35 m de pelo menos 3 paradas cuja descrição
     contém "W3 NORTE", ou seja, percorre a via em vez de só cruzá-la.

Uso:  python gerar_rotas.py        (só biblioteca padrão; ~5 requisições)
"""
import json
import math
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WFS = "https://geoserver.semob.df.gov.br/geoserver/semob/ows"
CAMADA_ROTAS = "semob:percuso das linhas"  # sic: é o nome da camada no GeoServer
GEOM_ROTAS = "geo_linhas_lin_31983"
CAMADA_PARADAS = "semob:Paradas de onibus"
CAMADA_HORARIOS = "semob:Horários das Linhas"
PARADAS_QI6 = ("2293", "2294")  # uma em cada sentido da EPPN
PARADA_REFERENCIA = "2293"  # a única desenhada no mapa
ROTULO_REFERENCIA = "SHIN QI 6"
RAIO_M = 35
MIN_PARADAS_W3 = 3
TOLERANCIA_SIMPLIFICACAO_M = 4
SAIDA = Path(__file__).with_name("rotas.js")


def wfs(camada, cql=None, srs=None, campos=None):
    q = {"service": "WFS", "version": "1.0.0", "request": "GetFeature",
         "outputFormat": "application/json", "typeName": camada}
    if cql:
        q["CQL_FILTER"] = cql
    if srs:
        q["srsName"] = srs
    if campos:
        q["propertyName"] = ",".join(campos)
    with urllib.request.urlopen(WFS + "?" + urllib.parse.urlencode(q), timeout=120) as r:
        return json.load(r)["features"]


def lista_cql(valores):
    return ",".join(f"'{v}'" for v in valores)


def partes(geom):
    return geom["coordinates"] if geom["type"] == "MultiLineString" else [geom["coordinates"]]


def dist_ponto_segmento(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    l2 = vx * vx + vy * vy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / l2))
    return math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy)


def dist_min(p, geom):
    # coordenadas nativas EPSG:31983 (UTM 23S): distância plana em metros
    return min(dist_ponto_segmento(p, a, b) for parte in partes(geom) for a, b in zip(parte, parte[1:]))


def simplificar(coords, tol_m):
    """Douglas-Peucker iterativo sobre [lon, lat], medindo em metros locais."""
    k = math.cos(math.radians(15.76))
    xy = [(lon * 111320 * k, lat * 110574) for lon, lat in coords]
    manter = [False] * len(coords)
    manter[0] = manter[-1] = True
    pilha = [(0, len(coords) - 1)]
    while pilha:
        i, j = pilha.pop()
        dmax, idx = 0.0, None
        for m in range(i + 1, j):
            d = dist_ponto_segmento(xy[m], xy[i], xy[j])
            if d > dmax:
                dmax, idx = d, m
        if idx is not None and dmax > tol_m:
            manter[idx] = True
            pilha += [(i, idx), (idx, j)]
    return [[round(lat, 5), round(lon, 5)] for (lon, lat), m in zip(coords, manter) if m]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    qi6 = wfs(CAMADA_PARADAS, f"parada IN ({lista_cql(PARADAS_QI6)})")
    if len(qi6) != len(PARADAS_QI6):
        sys.exit(f"Esperava {len(PARADAS_QI6)} paradas da QI 6, vieram {len(qi6)}.")

    perto = " OR ".join(
        f"DWITHIN({GEOM_ROTAS}, POINT({p['geometry']['coordinates'][0]} {p['geometry']['coordinates'][1]}), {RAIO_M}, meters)"
        for p in qi6)
    candidatas = wfs(CAMADA_ROTAS, f"situacao = 'ATIVA' AND ({perto})",
                     campos=["cd_linha", "lin_sentido", "tx_linha", GEOM_ROTAS])
    paradas_w3 = wfs(CAMADA_PARADAS, "descricao LIKE '%W3 NORTE%' AND situacao = 'ATIVA'")
    print(f"{len(candidatas)} itinerários passam pela QI 6; {len(paradas_w3)} paradas oficiais na W3 Norte.\n")

    aprovadas = {}
    for f in sorted(candidatas, key=lambda f: f["properties"]["cd_linha"]):
        p = f["properties"]
        n = sum(dist_min(s["geometry"]["coordinates"], f["geometry"]) <= RAIO_M for s in paradas_w3)
        ok = n >= MIN_PARADAS_W3
        print(f"  {'SIM' if ok else 'não':3}  {p['cd_linha']:>6} {p['lin_sentido']:9} {n:2} paradas W3 Norte  {p['tx_linha'].strip()}")
        if ok:
            aprovadas[(p["cd_linha"], p["lin_sentido"])] = n

    codigos = sorted({c for c, _ in aprovadas})
    if not codigos:
        sys.exit("Nenhuma linha atende ao critério; rotas.js não foi alterado.")
    linhas = {}
    for f in wfs(CAMADA_ROTAS, f"cd_linha IN ({lista_cql(codigos)})", srs="EPSG:4326"):
        p = f["properties"]
        chave = (p["cd_linha"], p["lin_sentido"])
        if chave not in aprovadas:
            continue
        linha = linhas.setdefault(p["cd_linha"], {"codigo": p["cd_linha"], "descricao": " ".join(p["tx_linha"].split()),
                                                  "tarifa": p.get("vl_tarifa"), "itinerarios": []})
        linha["itinerarios"].append({"sentido": p["lin_sentido"], "paradas_w3": aprovadas[chave],
                                     "trechos": [simplificar(t, TOLERANCIA_SIMPLIFICACAO_M) for t in partes(f["geometry"])]})

    # Tabela de horários programados: dias_semana é "SSSSSNN" (seg a dom), vigência em AAAA-MM-DD.
    for f in wfs(CAMADA_HORARIOS, f"cd_linha IN ({lista_cql(codigos)})"):
        p = f["properties"]
        if p["cd_linha"] in linhas:
            linhas[p["cd_linha"]].setdefault("horarios", []).append(
                [p["hr_prevista"], p["dias_semana"], p["dt_inicio_vigencia"][:10], (p["dt_final_vigencia"] or "")[:10]])
    for linha in linhas.values():
        linha["horarios"] = sorted(linha.get("horarios", []))

    def paradas_em(codigos_parada):
        return [{"codigo": p["properties"]["parada"], "descricao": " ".join(p["properties"]["descricao"].split()),
                 "lat": round(p["geometry"]["coordinates"][1], 6), "lon": round(p["geometry"]["coordinates"][0], 6)}
                for p in wfs(CAMADA_PARADAS, f"parada IN ({lista_cql(codigos_parada)})", srs="EPSG:4326")]

    dados = {"gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "criterio": f"passa em frente à SHIN QI 6 (EPPN) e percorre pelo menos {MIN_PARADAS_W3} "
                         f"paradas da W3 Norte",
             "linhas": [linhas[c] for c in codigos if c in linhas],
             "parada_referencia": {**paradas_em((PARADA_REFERENCIA,))[0], "rotulo": ROTULO_REFERENCIA}}
    SAIDA.write_text("// Gerado por gerar_rotas.py a partir do GeoServer da Semob-DF. Não editar à mão.\n"
                     "window.DADOS_ROTAS = " + json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + ";\n",
                     encoding="utf-8")
    print(f"\nLinhas selecionadas: {', '.join(codigos)}  ->  {SAIDA.name} ({SAIDA.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
