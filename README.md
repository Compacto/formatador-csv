# Dataplex Metadata Loader

## Visão Geral

O **Dataplex Metadata Loader** é uma aplicação web desenvolvida em **Python** e **Streamlit** para validar, padronizar e converter planilhas de metadados em arquivos CSV compatíveis com processos de ingestão no Dataplex.

A ferramenta foi criada para auxiliar equipes de **Governança de Dados**, **Data Stewardship** e **Engenharia de Dados**, garantindo que os arquivos submetidos estejam em conformidade com a estrutura esperada antes da carga.

---

# Objetivo da Aplicação

O objetivo principal da aplicação é:

* Validar templates de metadados em formato XLSX;
* Garantir conformidade estrutural dos arquivos;
* Aplicar regras de transformação e padronização;
* Gerar arquivos CSV compatíveis com processos de ingestão;
* Reduzir erros operacionais durante cargas de metadados.

---

# Funcionalidades

## Validação de Arquivos

* Upload de arquivos XLSX.
* Verificação de cabeçalhos obrigatórios.
* Detecção de colunas inesperadas.
* Validação estrutural antes da geração do CSV.
* Bloqueio da exportação quando existirem inconsistências.

## Padronização de Dados

* Canonicalização de cabeçalhos.
* Reconhecimento de aliases de colunas.
* Remoção de colunas vazias do tipo `Unnamed:`.
* Remoção de linhas completamente vazias.
* Preenchimento automático de campos ausentes com `NA`, quando aplicável.

## Validação de Conteúdo

* Validação de fragmentos HTML em campos específicos.
* Verificação de balanceamento de tags HTML.
* Verificação de presença de conteúdo textual válido.

## Exportação

* Conversão para CSV UTF-8.
* Separador padrão por vírgula.
* Aspas automáticas para campos contendo:

  * Espaços;
  * Vírgulas;
  * Quebras de linha;
  * Aspas;
  * Conteúdo HTML.
* Download do arquivo gerado pela interface.
* Salvamento local na pasta `output/`.

---

# Tecnologias Utilizadas

| Tecnologia   | Finalidade                           |
| ------------ | ------------------------------------ |
| Python 3.12+ | Linguagem principal                  |
| Streamlit    | Interface web                        |
| Pandas       | Manipulação e transformação de dados |
| OpenPyXL     | Leitura de arquivos XLSX             |

---

# Estrutura do Projeto

```text
project/
│
├── app.py
│
├── services/
│   ├── validator.py
│   ├── transformer.py
│   └── exporter.py
│
├── templates/
│   ├── *.xlsx
│
├── output/
│
├── requirements.txt
│
└── README.md
```

### Responsabilidades

| Arquivo          | Responsabilidade               |
| ---------------- | ------------------------------ |
| `app.py`         | Interface Streamlit            |
| `validator.py`   | Validações estruturais         |
| `transformer.py` | Transformações e padronizações |
| `exporter.py`    | Geração e exportação do CSV    |

---

# Requisitos

* Python 3.12 ou superior
* Pip
* Navegador moderno

---

# Instalação

Clone o repositório:

```bash
git clone <repositorio>
cd <repositorio>
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

# Como Executar Localmente

Execute:

```bash
streamlit run app.py
```

Após iniciar, acesse:

```text
http://localhost:8501
```

---

# Como Utilizar a Aplicação

## 1. Selecione o Tipo de Carga

Escolha o template correspondente ao processo desejado.

## 2. Faça Upload do XLSX

Envie um arquivo seguindo a estrutura do template oficial.

## 3. Execute a Validação

A aplicação verificará:

* Cabeçalhos obrigatórios;
* Estrutura do arquivo;
* Colunas inválidas;
* Conteúdo HTML quando aplicável.

## 4. Gere o CSV

Após aprovação das validações, o arquivo será convertido para CSV.

## 5. Faça o Download

O CSV poderá ser baixado diretamente pela interface.

---

# Tipos de Carga Suportados

## 1. Overview - Dataset

### Template

```text
overview-dataset-dominio.xlsx
```

### Arquivo Gerado

```text
overview-dataset-{domain}.csv
```

### Colunas Esperadas

```text
project
dataset
overview
tipo de ação
justificativa
```

### Colunas Exportadas

```text
project
dataset
overview
```

---

## 2. Overview - Table

### Template

```text
overview-table-dominio.xlsx
```

### Arquivo Gerado

```text
overview-table-{domain}.csv
```

### Colunas Esperadas

```text
project
dataset
table
overview
tipo de ação
justificativa
```

### Colunas Exportadas

```text
project
dataset
table
overview
```

---

## 3. Aspect - Dataset

### Template

```text
dataset-information.xlsx
```

### Arquivo Gerado

```text
dataset-information.csv
```

---

## 4. Aspect - Table/View

### Template

```text
table-information.xlsx
```

### Arquivo Gerado

```text
table-information.csv
```

---

## 5. Aspect - Column

### Template

```text
column-information.xlsx
```

### Arquivo Gerado

```text
column-information.csv
```

### Campo Opcional

```text
fl_meta_conf
```

Quando ausente, poderá receber valor padrão conforme as regras da aplicação.

---

## 6. Glossário

### Template

```text
glossary-insert.xlsx
```

### Arquivo Gerado

```text
glossary-insert.csv
```

### Validações Especiais

Campos:

* Description
* Overview

passam por validação de HTML.

---

# Regras de Validação e Transformação

## Canonicalização de Cabeçalhos

A aplicação normaliza nomes equivalentes de colunas.

Exemplo:

```text
Justificativa da Solicitação
↓
justificativa
```

---

## Limpeza de Estrutura

São removidos:

* Linhas totalmente vazias;
* Colunas vazias iniciadas por `Unnamed:`.

---

## Tratamento de Valores Vazios

Campos vazios nas colunas finais exportadas podem ser substituídos por:

```text
NA
```

---

## Validação de HTML

Os fragmentos HTML devem:

* Possuir tags balanceadas;
* Conter texto válido;
* Não apresentar estrutura inválida.

---

## Regras de Exportação

O CSV gerado utiliza:

```text
Encoding: UTF-8
Separador: ,
```

Campos contendo caracteres especiais são exportados entre aspas automaticamente.

---

# Exemplos

## Entrada

```csv
project,dataset,overview
prd_sales,sales_dataset,Descrição do dataset
```

## Saída

```csv
project,dataset,overview
prd_sales,sales_dataset,"Descrição do dataset"
```

---

# Nomenclatura dos Arquivos Gerados

| Tipo              | Saída                         |
| ----------------- | ----------------------------- |
| Overview Dataset  | overview-dataset-{domain}.csv |
| Overview Table    | overview-table-{domain}.csv   |
| Aspect Dataset    | dataset-information.csv       |
| Aspect Table/View | table-information.csv         |
| Aspect Column     | column-information.csv        |
| Glossário         | glossary-insert.csv           |

---

# Limitações

* Apenas arquivos `.xlsx` são aceitos.
* O arquivo deve seguir exatamente a estrutura do template correspondente.
* Colunas obrigatórias não podem ser removidas.
* Erros estruturais impedem a geração do CSV.
* HTML inválido bloqueia a exportação quando aplicável.

---

# Troubleshooting

## O arquivo não gera CSV

Verifique:

* Cabeçalhos obrigatórios;
* Colunas extras;
* Estrutura do template;
* Presença de HTML inválido.

---

## Aparecem erros de coluna inesperada

Confirme que o arquivo foi criado utilizando o template oficial correspondente.

---

## O upload não é aceito

Verifique se o arquivo possui extensão:

```text
.xlsx
```

---

## O conteúdo HTML foi rejeitado

Verifique:

* Tags abertas e fechadas corretamente;
* Ausência de elementos malformados;
* Presença de conteúdo textual válido.

---

# Segurança e Tratamento dos Dados

Os arquivos enviados são processados pela aplicação para execução das validações e transformações necessárias.

Os arquivos CSV gerados:

* Podem ser baixados diretamente pela interface;
* São gravados localmente na pasta `output/`.

A aplicação não realiza armazenamento permanente dos arquivos em serviços externos, bancos de dados ou provedores de nuvem. Todo o processamento e armazenamento ocorrem apenas no ambiente em que a aplicação está sendo executada.

---

# Licença

Definir conforme a política do projeto ou da organização responsável.
