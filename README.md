# Rote Assist 📊

Uma ferramenta automatizada construída em Python (com interface web via Streamlit) para o processamento de planilhas de rotas de vendedores. Ela calcula métricas de desempenho (aderência, horários de check-in/out, tempo no cliente) e oferece duas experiências distintas: um **resumo para compartilhamento** (WhatsApp, e-mail, PPT) e uma **análise criteriosa** com pontos positivos, negativos, gráficos de ranking e insights para tomada de decisão gerencial.

---

## 📁 Estrutura do Projeto

O projeto foi dividido em módulos com responsabilidades bem definidas para facilitar a manutenção. Abaixo, a explicação detalhada de cada arquivo:

---

### 1. `app.py`
**O Ponto de Entrada / Interface Web**

É aqui que toda a interface do usuário (UI) é construída utilizando o **Streamlit**. Este arquivo gerencia:

- A tela inicial com upload da planilha (`.xlsx` ou `.csv`), compartilhado entre as abas.
- Os campos de filtro globais: **Seleção de Gestor** e **Período via Calendário**.
- O botão inteligente para fechar o sistema (`os._exit(0)`).
- **Duas abas independentes:**
  - **📤 Resumo** — Gera o diagnóstico textual com emojis pronto para compartilhamento. Permite baixar o resultado como `.txt` ou `.png`.
  - **🔍 Análise** — Painel analítico completo para gestores (ver detalhes abaixo).
- Toda a lógica de renderização da aba Análise: cards HTML de pontos positivos/negativos, gráficos de ranking nativos do Streamlit, cards de insights e os botões de exportação em PNG e PDF.
- A função `_gerar_pdf_analise()` que produz o PDF da análise criteriosa usando `fpdf2`.

---

### 2. `config.py`
**O Coração das Regras de Nomenclatura**

Este arquivo armazena as configurações globais e o mapeamento "de-para" das colunas da planilha.

- O dicionário `COLUNAS` mapeia o nome interno usado pelo código (ex: `"aderencia"`) para o cabeçalho exato que aparece na planilha (ex: `"% Aderencia de Rota"`). Toda vez que o nome de uma coluna mudar na planilha de origem, basta atualizar aqui.
- `TEMPO_MINIMO_CLIENTE_MIN` — define o limiar mínimo de permanência no cliente em minutos. Se `None`, o sistema usa a média da própria equipe como referência.
- `FILTRAR_POR_GESTOR`, `SALVAR_TXT_AUTO`, `COPIAR_CLIPBOARD_AUTO` — flags para comportamentos opcionais.
- `FORMATO_PERIODO_EXEMPLO` — exemplo de período exibido na interface do terminal.

---

### 3. `loader.py`
**Limpeza e Padronização de Dados**

Este módulo atua como o "tradutor" dos dados brutos. Suas funções:

- Ler o arquivo enviado pelo Streamlit (objeto de memória) **ou** um caminho de arquivo no disco — suportando tanto `.xlsx` quanto `.csv`.
- Verificar se todas as colunas obrigatórias mapeadas no `config.py` existem, lançando erros claros com as colunas ausentes.
- Limpar e converter os dados:
  - Strings de porcentagem `"54%"` ou decimais `0.54` → `float 54.0`.
  - Strings de horário `"08:30"` ou objetos `datetime` → `datetime.time` → minutos desde meia-noite (para comparação matemática).
  - Valores numéricos com vírgula → inteiros.
- Entregar um `DataFrame` perfeitamente padronizado com os nomes internos definidos em `config.py`.
- Exporta a função `minutes_to_time_str()` usada por outros módulos para converter minutos de volta para o formato `"HH:MM"`.

---

### 4. `analyzer.py`
**O Cérebro da Operação (Regras de Negócio)**

Aqui acontece toda a matemática, análise estatística e classificação dos vendedores. O módulo recebe o DataFrame limpo do `loader.py` e retorna a estrutura `ResultadoAnalise` preenchida com todos os indicadores calculados.

**Dataclasses de dados:**
- `VendedorMetrica` — par nome/valor genérico (usado para aderência, tempo, check-in/out, etc.).
- `VendedorVisitasRemotas` — armazena nome, visitas remotas e visitas previstas de um vendedor.
- `VendedorRankingAderencia` — nome e aderência (para o ranking completo da equipe).
- `VendedorComparativo` — nome com contagens de visitas presenciais, remotas, não realizadas e previstas (para o gráfico comparativo).

**Métricas calculadas (16 no total):**

| # | Métrica | Classificação |
|---|---|---|
| 1 | Aderência à rota — média e quem está **abaixo** | ⚠️ Negativo |
| 2 | Check-in — quem chegou **depois** da média | ⚠️ Negativo |
| 3 | Check-out — quem saiu **antes** da média | ⚠️ Negativo |
| 4 | Tempo no cliente — quem ficou **abaixo** do limiar | ⚠️ Negativo |
| 5 | Visitas não realizadas — quem tem faltas | ⚠️ Negativo |
| 6 | Apenas visitas remotas — ponto de atenção crítico | ⚠️ Atenção |
| 7 | Visitas remotas — quem está **acima** da média | 📊 Info |
| 8 | Aderência — quem está **acima** da média | ✅ Positivo |
| 9 | Check-in — quem chegou **antes** da média (pontual) | ✅ Positivo |
| 10 | Check-out — quem ficou **mais tarde** (dedicação) | ✅ Positivo |
| 11 | Tempo no cliente — quem está **acima** do limiar | ✅ Positivo |
| 12 | Sem faltas — quem cumpriu 100% das visitas | ✅ Positivo |
| 13 | Total de vendedores analisados | 📊 Info |
| 14 | Ranking completo de aderência (ordenado) | 📊 Ranking |
| 15 | Ranking de visitas não realizadas (todos) | 📊 Ranking |
| 16 | Comparativo presencial/remoto/não realizado | 📊 Ranking |

---

### 5. `formatter.py`
**Gerador do Texto de Saída para Compartilhamento**

Este módulo recebe a estrutura `ResultadoAnalise` e a "traduz" para um texto humano formatado com emojis, pronto para colar no WhatsApp ou e-mail.

- Injeta os emojis adequados (🔻, 📤, 📥, ⏳, ❌, ⚠️, ✅, 📞) em cada seção.
- Monta o cabeçalho com nome do gestor e período apurado.
- Exibe mensagens alternativas positivas quando não há pontos de atenção (ex: "✅ Todos os vendedores estão acima ou na média...").
- Retorna uma única `str` pronta para exibir na tela, salvar em `.txt` ou usar como base para a imagem.

---

### 6. `image_generator.py`
**Estúdio Visual — Imagem do Resumo**

Responsável por gerar o arquivo PNG do **resumo textual** para download.

- Monta um HTML5 completo com CSS corporativo (design de cards claros, fontes modernas, cores de status).
- Usa a biblioteca `html2image` (que aciona o navegador instalado na máquina em modo headless) para renderizar o HTML e capturar um PNG em alta resolução (`800×1000 px`).
- Retorna os bytes da imagem diretamente para o Streamlit, sem salvar arquivos permanentes em disco (usa `tempfile.TemporaryDirectory`).

---

### 7. `insights.py`
**Motor de Insights para Tomada de Decisão**

Módulo dedicado a transformar os dados numéricos em **frases de diagnóstico gerencial** geradas automaticamente por regras de negócio (sem IA).

- A função `gerar_insights(resultado)` analisa o `ResultadoAnalise` e retorna uma lista de dicts com: `tipo` (`positivo | negativo | atencao | neutro`), `icone`, `titulo` e `detalhe`.
- **Insights gerados:**
  - % da equipe abaixo da meta de aderência + recomendação de ação.
  - Spread (diferença em p.p.) entre o melhor e o pior vendedor — alerta quando ≥ 30 p.p.
  - Quantidade e % de vendedores com check-in tardio.
  - Quantidade e % com check-out antecipado.
  - % da equipe com tempo insuficiente no cliente.
  - Concentração de faltas: os 3 maiores concentram X% do total — para priorizar ação.
  - Alerta crítico de vendedores com apenas visitas remotas.
  - Destaque do melhor vendedor como referência positiva para o time.
  - Validações de equipe perfeita (ex: 100% acima da meta, zero faltas).

---

### 8. `analysis_image_generator.py`
**Estúdio Visual — Imagem da Análise Criteriosa**

Gera o PNG premium da **aba Análise** para exportação.

- Tema dark (fundo escuro gradiente `#0f172a → #1e293b`) com tipografia Inter.
- Seção de **Pontos Positivos** — cards com borda verde sobre fundo escuro.
- Seção de **Pontos Negativos** — cards com borda vermelha/amarela.
- **Ranking de Aderência** — tabela com barras de progresso HTML renderizadas.
- **Insights para Decisão** — todos os insights do `insights.py`.
- Dimensão: `800×2200 px`, adequada para capturas longas.
- Mesmo padrão do `image_generator.py`: usa `html2image` + `tempfile`, sem arquivos permanentes.

---

### 9. `main.py`
**Interface de Terminal (CLI)**

Interface interativa alternativa via linha de comando usando a biblioteca `rich`, para uso sem abrir o navegador.

- Exibe banners coloridos, tabelas formatadas e prompts interativos no terminal.
- Solicita o caminho do arquivo, a seleção de gestor e o período manualmente.
- Chama os mesmos módulos `loader`, `analyzer` e `formatter` que o `app.py`.
- Exibe o resumo final em um painel estilizado no próprio terminal.
- **Não gera imagens** — focado apenas no texto de saída.

---

### 10. `iniciar.bat`
**O Atalho Prático**

Um script em lote do Windows que executa o comando `streamlit run app.py`. Serve para que o usuário não precise abrir o terminal manualmente — basta um duplo clique para ligar o servidor e abrir o app no navegador.

---

### 11. `requirements.txt`
**Gerenciador de Dependências**

Lista todas as bibliotecas externas necessárias para o sistema rodar:

| Biblioteca | Uso |
|---|---|
| `pandas` | Leitura e manipulação da planilha |
| `openpyxl` | Suporte a arquivos `.xlsx` |
| `rich` | Interface colorida do terminal (CLI) |
| `pyperclip` | Cópia para área de transferência (CLI) |
| `streamlit` | Interface web |
| `Pillow` | Manipulação de imagens |
| `html2image` | Renderização de HTML → PNG |
| `fpdf2` | Geração de arquivos PDF |
| `pyinstaller` | Empacotamento em executável `.exe` |

---

## 🚀 Como o programa funciona?

O fluxo da aplicação do início ao fim ocorre da seguinte maneira:

1. **Início:** O usuário clica duas vezes no `iniciar.bat`, o que liga o servidor local e abre o app no navegador.
2. **Entrada de Dados:** Arrasta uma planilha de visitas para dentro da tela e escolhe o período e gestor nos filtros.
3. **Processamento Oculto:**
   - O `loader.py` higieniza os dados da planilha.
   - O `analyzer.py` calcula todas as 16 métricas e classifica os vendedores.
4. **Escolha da Experiência — duas abas disponíveis:**

   - **📤 Aba Resumo:** Clique em "Gerar Resumo" para obter o diagnóstico textual formatado com emojis. Exporte como `.txt` ou `.png` corporativo.

   - **🔍 Aba Análise:** Clique em "Gerar Análise Criteriosa" para obter:
     - Cards visuais de **pontos positivos** (quem se destaca) e **pontos negativos** (quem precisa de atenção).
     - **Gráficos de ranking** de aderência, faltas e comparativo presencial/remoto.
     - **Insights automáticos** com linguagem gerencial para apoiar decisões.
     - Exportação como **PNG** (imagem dark premium) ou **PDF** (documento formal).

5. **Fim:** Ao clicar no botão `❌ Fechar`, o servidor é desconectado e a memória é liberada.
