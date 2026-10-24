# Ônibus W3 Norte · SHIN QI 6

Mapa com a posição ao vivo dos ônibus que passam pela **W3 Norte** e pela
**EPPN em frente à SHIN QI 6** (Lago Norte, Brasília). Cada ônibus aparece com
o número da linha e uma seta apontando o sentido do movimento, calculado pelo
deslocamento entre duas leituras. Enquanto não houver duas leituras, a seta
fica cinza e sem direção.

O mapa destaca a parada 2293 ("SHIN APOS ENTRADA DA QI/QL 06 EPPN"), rotulada
**SHIN QI 6**. Para cada linha, o painel mostra quantos ônibus estão em trânsito
e a próxima saída programada da origem (o primeiro trecho do percurso). Um
pedestre marca onde você está, pelo GPS do celular; a posição só serve para
desenhar o pedestre e não sai do aparelho.

## Linhas

| Linha | Itinerário (Semob) | Paradas da W3 Norte no itinerário |
|---|---|---|
| 0.136 | Rodoviária do Plano Piloto / W3 Norte / Clube do Congresso (Hospital Sarah) / L2 Norte | 28 de 32 |
| 136.2 | Terminal Asa Sul / W3 Sul - Norte / Lago Norte (Hospital Sarah) | 32 de 32 |
| 136.5 | Rod. Piloto / L2 Norte / C. Congresso (Hosp. Sarah) / W3 Norte | 28 de 32 |

Critério, aplicado por `gerar_rotas.py` sobre o itinerário georreferenciado
oficial da Semob:

1. o itinerário passa a até 35 m das paradas **2293** ("SHIN APOS ENTRADA DA
   QI/QL 06 EPPN") ou **2294** ("SHIN QI 6 EPPN"), uma em cada sentido da EPPN;
2. o itinerário passa a até 35 m de pelo menos 3 das 32 paradas cuja
   descrição contém "W3 NORTE". Quem só cruza a W3 pega no máximo uma.

As demais linhas com "136" no número ficam de fora porque não passam em frente
à QI 6 ou não percorrem a W3 Norte.

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
(o filtro espacial em torno das paradas da QI 6 roda no próprio servidor).
Ele imprime a avaliação de cada candidata e reescreve `rotas.js`. As linhas
monitoradas pela página saem desse arquivo, então não há lista para editar à
mão. Os limiares (`RAIO_M`, `MIN_PARADAS_W3`) e as paradas de referência
(`PARADAS_QI6`) estão no topo do script.

## Fontes de dados

| O quê | Endereço |
|---|---|
| Posição por linha (usado a cada 15 s) | `https://www.sistemas.dftrans.df.gov.br/gps/linha/{linha}/geo/recent` (GeoJSON) |
| Posição de toda a frota (reserva, ~400 KB) | `https://www.sistemas.dftrans.df.gov.br/service/gps/operacoes` |
| Itinerários georreferenciados | GeoServer da Semob, camada `semob:percuso das linhas` (WFS, EPSG:31983) |
| Paradas | GeoServer da Semob, camada `semob:Paradas de onibus` |
| Horários programados | GeoServer da Semob, camada `semob:Horários das Linhas` (copiados para `rotas.js`, porque o GeoServer não libera leitura pelo navegador) |

Não encontrei documentação oficial dos serviços de posição: podem mudar de
endereço ou de formato sem aviso.

## Limitações

- Só aparecem ônibus que a Semob informa como operando numa dessas linhas.
  Veículos sem linha informada no feed não podem ser atribuídos.
- A posição é a última que o ônibus transmitiu. Leituras com mais de 3 minutos
  aparecem esmaecidas; com mais de 30 minutos, somem.
- A próxima saída é a do horário programado, não a do ônibus real. A tabela
  da Semob não diz em que parada a viagem começa; o site assume o primeiro
  terminal do percurso. Feriados não são tratados. A 136.2 tem poucas viagens
  programadas (nenhuma no domingo).
- Os horários ficam congelados em `rotas.js`: rode `gerar_rotas.py` de novo
  quando a Semob mudar a tabela.
- O pedestre só aparece se o navegador tiver permissão de localização; se ela
  for negada, o botão do pedestre fica apagado.
