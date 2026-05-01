# CLAUDE.md

## Projeto

Sistema web em Python + Django para importar comprovantes de apostas em PDF das loterias da Caixa Econômica Federal, extrair os dados relevantes, armazená-los em banco relacional e disponibilizar consultas, filtros e estatísticas em páginas renderizadas pelo Django.

O sistema deve ler automaticamente os arquivos PDF localizados na pasta `/pdfs`, identificar novos arquivos, processá-los sem duplicidade e manter o banco sempre atualizado.

## Objetivo

Permitir a análise de:

- total gasto em apostas
- frequência dos números jogados
- distribuição por tipo de jogo
- estatísticas comparativas com resultados oficiais da Mega-Sena

O sistema é de uso local, com foco em automação, rastreabilidade, simplicidade de manutenção e interface objetiva.

## Escopo funcional

- Ler arquivos PDF da pasta `/pdfs`
- Importar o conteúdo de cada arquivo
- Separar os dados por tipo de jogo
- Gravar tudo em banco de dados
- Atualizar o banco ao encontrar novos PDFs
- Evitar duplicidade de importação
- Exibir páginas Django com filtros, tabela e estatísticas
- Importar resultados oficiais da Mega-Sena
- Gerar estatísticas dos números mais sorteados na Mega-Sena

## Tecnologias

- Python 3.10+
- Django
- Banco de dados: SQLite ou MySQL
- Extração de PDF: `pdfplumber` como primeira opção; `pypdf` como apoio, se necessário
- Testes: `pytest` + `pytest-django`
- Lint/format: `ruff`

## Diretrizes técnicas

- Usar Django ORM como padrão
- Manter compatibilidade com SQLite e MySQL
- Evitar SQL específico de banco sem necessidade real
- Usar management commands do Django para rotinas de importação e atualização
- Manter parsing, persistência e apresentação separados
- Preservar texto bruto extraído no MVP para auditoria

## Fonte dos arquivos

- Pasta principal de entrada: `/pdfs`
- Atualmente há 119 arquivos PDF
- Os PDFs possuem formatação em comum
- Os arquivos correspondem a comprovantes/prints de apostas da Caixa Econômica Federal

## Regra de atualização

Sempre que o sistema for iniciado, ele deve verificar a pasta `/pdfs` e importar somente arquivos novos.

A identificação de duplicidade deve ser feita preferencialmente por hash do arquivo, e não apenas pelo nome.

## Regra de nomenclatura dos arquivos

Os arquivos atualmente estão nomeados no formato `ddmmaaaa`.

Deve existir uma etapa inicial para tratar essa inconsistência e, quando aplicável, renomear os arquivos para o formato `aaaammdd`, de forma segura e auditável.

Regras:
- nunca sobrescrever arquivos existentes
- registrar nome original e nome novo
- sinalizar casos ambíguos para revisão manual

## Dados esperados no PDF

O parser deve procurar, no mínimo:

- nome do jogo, por exemplo:
  - Dia de Sorte
  - Dupla-Sena
  - Lotofácil
  - +Milionária
  - Mega-Sena
- números apostados
- valor da aposta
- data do jogo, quando identificável
- demais campos estáveis encontrados nos comprovantes

## Estrutura sugerida

```text
loteria/
├─ manage.py
├─ CLAUDE.md
├─ pyproject.toml
├─ .env
├─ .venv/
├─ core/
├─ importacao/
├─ apostas/
├─ resultados/
├─ templates/
├─ static/
├─ tests/
├─ pdfs/
└─ docs/
```

## Apps principais

### `importacao`
Responsável por:
- localizar PDFs
- validar arquivos
- calcular hash
- identificar novos arquivos
- renomear arquivos quando necessário
- extrair texto
- acionar parser
- registrar logs e erros

### `apostas`
Responsável por:
- models de domínio
- filtros
- estatísticas de números jogados
- consultas
- páginas renderizadas

### `resultados`
Responsável por:
- importar resultados oficiais da Mega-Sena
- armazenar concursos
- gerar estatísticas dos números mais sorteados

## Modelagem inicial sugerida

### `ArquivoImportado`
- nome_arquivo_original
- nome_arquivo_atual
- caminho_arquivo
- hash_arquivo
- data_detectada
- data_importacao
- status_importacao
- mensagem_erro
- texto_extraido
- quantidade_paginas

### `TipoJogo`
- nome
- slug
- ativo

### `Comprovante`
- arquivo_importado
- tipo_jogo
- data_jogo
- valor_total_aposta
- codigo_autenticacao
- observacoes

### `Aposta`
- comprovante
- sequencia
- descricao
- valor_aposta

### `NumeroApostado`
- aposta
- ordem
- numero

### `ResultadoMegaSena`
- concurso
- data_apuracao
- dezena_1
- dezena_2
- dezena_3
- dezena_4
- dezena_5
- dezena_6

### `LogImportacao`
- arquivo_relacionado
- etapa
- nivel
- mensagem
- data_hora

## Interface obrigatória

A interface principal em Django deve conter:

### Filtros
- intervalo de data do jogo
- tipo de jogo
- filtro “ver outros” (deixar preparado para detalhamento posterior)

### Elementos
- tabela principal com os dados importados
- label no canto superior direito com o total gasto, calculado pela soma do campo valor da aposta conforme os filtros ativos
- quadro com estatísticas dos números mais escolhidos, conforme os jogos
- quadro com estatísticas dos números mais sorteados da Mega-Sena

## Proposta de tabela principal

Colunas sugeridas:
- data do jogo
- tipo de jogo
- números jogados
- quantidade de números
- valor da aposta
- nome do arquivo
- status
- link para detalhe

## Páginas principais

### Dashboard
- total de arquivos importados
- total gasto
- total por tipo de jogo
- números mais escolhidos
- números mais sorteados da Mega-Sena

### Listagem
- filtros
- tabela principal
- total gasto conforme filtros

### Detalhe do comprovante
- dados do arquivo
- tipo de jogo
- data do jogo
- números apostados
- valor da aposta
- texto extraído
- inconsistências, se houver

### Erros de importação
- arquivos com falha
- etapa da falha
- mensagem de erro
- status de reprocessamento

### Estatísticas
- números mais jogados por tipo de jogo
- frequência total por número
- recortes por período
- comparação com resultados oficiais da Mega-Sena

### Admin
- consultar comprovantes
- revisar arquivos importados
- revisar logs
- revisar resultados oficiais

## Resultados oficiais da Mega-Sena

O sistema deve buscar ou importar os resultados oficiais da Mega-Sena a partir da página da Caixa indicada no roteiro do projeto.

Observações:
- o arquivo disponibilizado é um ZIP
- o botão citado no roteiro é “Resultados da Mega-Sena por ordem crescente”
- essa importação deve ficar restrita inicialmente à Mega-Sena

## Estratégia de processamento

### Etapas
1. localizar arquivos na pasta `/pdfs`
2. validar PDF
3. calcular hash
4. identificar se o arquivo já foi importado
5. renomear, quando necessário
6. extrair texto bruto
7. normalizar conteúdo
8. aplicar parser
9. validar campos mínimos
10. persistir dados
11. registrar logs
12. atualizar estatísticas

## Estratégia de parsing

Separar em camadas:

- descoberta de arquivos
- leitura do PDF
- normalização do texto
- parser de domínio
- validação
- persistência

Regras:
- não colocar parsing em views
- não espalhar regex sem organização
- centralizar parsing em services
- toda correção baseada em caso real deve gerar teste
- manter o parser tolerante a pequenas variações, mas explícito em caso de erro

## Commands esperados

```bash
python manage.py import_pdfs
python manage.py import_pdfs --path pdfs
python manage.py reprocessar_importacoes
python manage.py importar_resultados_megasena
python manage.py atualizar_estatisticas
```

## Organização interna recomendada

```text
importacao/
├─ models.py
├─ admin.py
├─ management/commands/
├─ services/
│  ├─ file_discovery.py
│  ├─ file_rename.py
│  ├─ hash_service.py
│  ├─ pdf_reader.py
│  ├─ parser.py
│  ├─ normalizer.py
│  └─ importer.py
└─ tests/

apostas/
├─ models.py
├─ admin.py
├─ views.py
├─ urls.py
├─ forms.py
├─ selectors.py
├─ services/
│  ├─ statistics.py
│  └─ filters.py
├─ templates/apostas/
└─ tests/

resultados/
├─ models.py
├─ admin.py
├─ management/commands/
├─ services/
│  ├─ caixa_downloader.py
│  ├─ zip_extractor.py
│  ├─ megasena_importer.py
│  └─ megasena_statistics.py
└─ tests/
```

## Convenções de código

- usar type hints sempre que possível
- manter views leves
- separar regras de negócio em services/selectors
- usar nomes explícitos
- priorizar legibilidade
- evitar abstração prematura
- usar Django nativo antes de adicionar dependências extras
- criar testes para parser, importação, estatísticas e páginas principais

## Testes mínimos

- detecção de novos PDFs
- prevenção de duplicidade por hash
- renomeação de `ddmmaaaa` para `aaaammdd`
- extração de texto
- parsing do nome do jogo
- parsing dos números apostados
- parsing do valor da aposta
- importação completa de comprovante válido
- tratamento de PDF inválido
- importação dos resultados da Mega-Sena
- cálculo dos números mais jogados
- cálculo dos números mais sorteados
- renderização dos filtros e da tabela principal

## Ambiente de desenvolvimento

O ambiente virtual deste projeto fica dentro da própria pasta `loteria/.venv`, o que deve ser mantido como padrão.

Diretrizes:
- instalar dependências sempre nesse ambiente
- não depender de ambiente virtual compartilhado entre projetos
- documentar comandos de setup no projeto
- manter `.env.example` atualizado

## Decisões ainda em aberto

- definir se o banco principal será SQLite ou MySQL no ambiente final
- detalhar o comportamento do filtro “ver outros” (hoje só placeholder no formulário)
- validar o layout final da tabela principal

## Decisões resolvidas durante a implementação inicial

- **Texto selecionável nos PDFs**: NÃO. Pelo menos `03012026.pdf` é só imagem;
  ambos pdfplumber e pypdf retornam texto vazio. O importer marca esses
  arquivos como `falha` com mensagem clara. OCR fica para uma fase futura.
- **Apostas por arquivo**: cada PDF é uma “compra” da Caixa com MÚLTIPLOS
  comprovantes (um por tipo de jogo) e várias apostas dentro de cada
  comprovante. Os modelos seguem essa hierarquia.
- **Números apostados**: dependem do layout do PDF.
  - Layout novo (~2024+): só aparece `<concurso> Efetivada R$ <valor>`. As
    dezenas estão em imagem; ficam para OCR.
  - Layout antigo (~2022): as dezenas APARECEM no texto extraído e são
    persistidas em `NumeroApostado`. Exceção: Super Sete, em que o cabeçalho
    fixo `11 22 33 44 55 66 77` é descartado e os dígitos escolhidos não são
    capturados (impacto: poucos comprovantes).
  - A coluna “Situação da Aposta” do layout novo é descartada — todos os
    comprovantes nesses PDFs são “Efetivada”.
- **Download do ZIP da Mega-Sena**: o command `importar_resultados_megasena`
  suporta `--html` (arquivo extraído manualmente), `--zip` (ZIP local) e
  `--download` (baixa via `MEGASENA_RESULTS_URL` no `.env`). Por padrão fica
  manual; basta configurar a URL para automatizar.

## Ordem de implementação

1. criar projeto Django base
2. criar apps `importacao`, `apostas` e `resultados`
3. configurar SQLite inicialmente
4. criar models principais
5. implementar descoberta de arquivos e hash
6. implementar renomeação segura
7. extrair texto de amostras reais
8. mapear campos reais do PDF
9. implementar parser inicial
10. persistir importação completa
11. criar listagem com filtros
12. exibir total gasto
13. criar estatísticas dos números jogados
14. importar resultados da Mega-Sena
15. criar estatísticas dos números mais sorteados
16. refinar páginas e tratamento de erros

## Instruções para o Claude Code

- sempre ler este `CLAUDE.md` antes de propor alterações
- usar este arquivo como fonte principal de contexto do projeto
- priorizar o MVP funcional
- inspecionar PDFs reais antes de alterar o parser
- preservar vínculo entre arquivo original, texto extraído e dados estruturados
- implementar páginas Django conforme os requisitos definidos aqui
- manter compatibilidade com SQLite e MySQL
- evitar complexidade desnecessária no front-end
- criar testes para toda correção relevante no parser
- explicar impacto antes de grandes refatorações

## Primeiras tarefas

- criar o projeto Django base
- criar apps `importacao`, `apostas` e `resultados`
- configurar models iniciais
- criar command `import_pdfs`
- implementar renomeação segura dos arquivos
- extrair texto de uma amostra de PDFs
- mapear campos reais
- criar listagem inicial com filtro de data e tipo de jogo
- exibir total gasto
- iniciar a importação dos resultados oficiais da Mega-Sena