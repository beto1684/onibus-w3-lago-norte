# Ônibus W3 Norte · SHIN QI 8 / QI 6

Mapa com a posição ao vivo dos ônibus que passam pela **W3 Norte** e pela
**EPPN em frente à SHIN QI 8** (Lago Norte, Brasília). Cada ônibus aparece com
o número da linha e uma seta apontando o sentido do movimento, calculado pelo
deslocamento entre duas leituras. Enquanto não houver duas leituras, a seta
fica cinza e sem direção.

O mapa destaca a parada da **SHIN QI 6** como referência; as distâncias são
medidas até ela. A escolha das linhas continua baseada na QI 8.

## Linhas

| Linha | Itinerário (Semob) | Paradas da W3 Norte no itinerário |
|---|---|---|
| 0.136 | Rodoviária do Plano Piloto / W3 Norte / Clube do Congresso (Hospital Sarah) / L2 Norte | 28 de 32 |
| 136.2 | Terminal Asa Sul / W3 Sul - Norte / Lago Norte (Hospital Sarah) | 32 de 32 |
| 136.5 | Rod. Piloto / L2 Norte / C. Congresso (Hosp. Sarah) / W3 Norte | 28 de 32 |

Critério, aplicado por `gerar_rotas.py` sobre o itinerário georreferenciado
oficial da Semob:

1. o itinerário passa a até 35 m das paradas **2295** ("SHIN APOS ENTRADA
   QI/QL 08 EPPN") ou **2296** ("SHIN QI 08 EPPN");
2. o itinerário passa a até 35 m de pelo menos 3 das 32 paradas cuja
   descrição contém "W3 NORTE". Quem só cruza a W3 pega no máximo uma.

Dezessete itinerários passam em frente à QI 8, mas só esses três passam
pela W3 Norte; os demais têm **zero** paradas da W3. Linhas com "136" no
número que ficam de fora: 136.1, 136.4, 136.6, 136.7, 136.9 (não passam na
QI 8) e 136.3, 136.8 (passam na QI 8, mas não na W3 Norte).

## Como abrir

- **No computador, direto:** dê dois cliques em `index.html`. Nesse modo o
  mapa de fundo é o da Esri, porque o servidor do OpenStreetMap bloqueia
  pedidos de páginas abertas do disco (sem `Referer`).
- **No computador, com o mapa do OpenStreetMap:** na pasta do site, rode
  `python -m http.server 8000` e abra <http://localhost:8000>.
- **No celular:** publique a pasta como site estático (por exemplo, GitHub
  Pages). O servidor da Semob responde a qualquer origem (CORS), então não
  precisa de backend.

## Atualizar as rotas

Quando a Semob mudar itinerários, rode:

```
python gerar_rotas.py
```

O script usa só a biblioteca padrão e faz cerca de 5 requisições ao GeoServer
(o filtro espacial em torno das paradas da QI 8 roda no próprio servidor).
Ele imprime a avaliação de cada candidata e reescreve `rotas.js`. As linhas
monitoradas pela página saem desse arquivo, então não há lista para editar à
mão. Os limiares (`RAIO_M`, `MIN_PARADAS_W3`) e as paradas de referência
(`PARADAS_QI8`) estão no topo do script.

## Fontes de dados

| O quê | Endereço |
|---|---|
| Posição por linha (usado a cada 15 s) | `https://www.sistemas.dftrans.df.gov.br/gps/linha/{linha}/geo/recent` (GeoJSON) |
| Posição de toda a frota (reserva, ~400 KB) | `https://www.sistemas.dftrans.df.gov.br/service/gps/operacoes` |
| Itinerários georreferenciados | GeoServer da Semob, camada `semob:percuso das linhas` (WFS, EPSG:31983) |
| Paradas | GeoServer da Semob, camada `semob:Paradas de onibus` |

Não encontrei documentação oficial dos serviços de posição: podem mudar de
endereço ou de formato sem aviso.

## Limitações

- Só aparecem ônibus que a Semob informa como operando numa dessas linhas.
  Veículos sem linha informada no feed não podem ser atribuídos.
- A posição é a última que o ônibus transmitiu. Leituras com mais de 3 minutos
  aparecem esmaecidas; com mais de 30 minutos, somem.
- A distância até a QI 6 mostrada no painel é em linha reta, não pelo
  itinerário.
