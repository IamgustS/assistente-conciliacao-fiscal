# 🧾 Assistente de Extração e Conciliação de Notas Fiscais e Recibos

> Solução de IA multimodal para automação financeira: digitalização visual, validação contábil e conciliação matemática de cupons fiscais, recibos e notas fiscais (PDF e imagens).

---

## 🎯 Problema Real Resolvido
Pequenos negócios, autônomos, freelancers e setores financeiros gastam horas digitando manualmente dados de recibos amassados, comprovantes térmicos e notas fiscais. Esse processo manual é lento, repetitivo e suscetível a erros humanos de digitação e fechamento contábil.

## 🚀 O Que Este Assistente Faz
1. **Leitura Visual Inteligente (Vision AI / Multimodal)**:
   - Suporte a fotos de celulares, papéis amassados, cupons fiscais térmicos (NFC-e / SAT), recibos comerciais e arquivos PDF (DANFE).
   - Extrai automaticamente: Estabelecimento Emissor, CNPJ/CPF, Data, Hora, Lista de Itens (Qtd, Unitário, Total), Descontos, Acréscimos/Gorjetas e Valor Total Final.
   - Categorização inteligente automática da despesa (ex: Alimentação, Transporte, TI/Software, Escritório).
2. **Motor de Conciliação Contábil & Matemática**:
   - Valida formalmente se a soma dos itens deduzindo descontos e somando acréscimos bate exatamente com o total cobrado:
     $$\sum (\text{Itens}) - \text{Descontos} + \text{Acréscimos} = \text{Total Declarado}$$
   - Alerta visual imediato para divergências de centavos ou erros de cálculo no recibo.
   - Validação algorítmica de CNPJ e CPF (dígitos verificadores oficiais da Receita Federal).
3. **Persistência & Exportação**:
   - Banco de dados local SQLite com auditoria de conciliação.
   - Exportação para planilha Microsoft Excel (.xlsx) com múltiplas abas formatadas.
   - Exportação para CSV (UTF-8 com BOM) pronto para ERPs e sistemas contábeis.

---

## 🛠️ Stack Tecnológica
- **Linguagem**: Python 3.12
- **Visão Computacional & LLM**: Google Gemini Multimodal (`google-genai` SDK) com Structured Outputs (Pydantic)
- **Modelos de Dados**: Pydantic v2
- **Banco de Dados**: SQLite3 com Foreign Keys e auditoria
- **Processamento de Dados**: Pandas, OpenPyXL, Pillow, PyPDF
- **Interface Gráfica (UI)**: Streamlit
- **Interface de Terminal (CLI)**: Rich CLI

---

## 📂 Estrutura do Projeto
```
NF/
├── app.py                      # Interface Web moderna em Streamlit
├── cli.py                      # Linha de comando para automação em lote
├── extractor.py                # Motor de extração visual via Vision LLM (Gemini)
├── conciliator.py              # Validação de CNPJ/CPF e regras matemáticas de conciliação
├── database.py                 # Camada de persistência SQLite
├── exporter.py                 # Exportador para Excel multi-abas e CSV contábil
├── models.py                   # Schemas Pydantic tipados
├── config.py                   # Configurações e diretórios
├── generate_sample_receipts.py # Gerador de comprovantes sintéticos para testes
├── test_conciliator.py         # Bateria de testes unitários automatizados
├── exemplos/                   # Imagens e PDFs prontos para demonstração
│   ├── recibo_posto_conciliado.png
│   ├── recibo_restaurante_divergente.png
│   └── danfe_papelaria_tech.pdf
├── data/                       # Banco de dados e relatórios gerados
└── requirements.txt            # Dependências do projeto
```

---

## ⚡ Como Executar

### 1. Iniciar o Painel Web (Streamlit)
```powershell
.venv\Scripts\streamlit run app.py
```
Acesse no seu navegador: `http://localhost:8501`

### 2. Usar via Linha de Comando (CLI)
- **Processar um comprovante individual:**
  ```powershell
  .venv\Scripts\python.exe cli.py processar exemplos\recibo_posto_conciliado.png
  ```
- **Processar uma pasta inteira em lote:**
  ```powershell
  .venv\Scripts\python.exe cli.py lote exemplos\
  ```
- **Listar histórico de notas salvas:**
  ```powershell
  .venv\Scripts\python.exe cli.py listar
  ```
- **Exportar relatório em Excel ou CSV:**
  ```powershell
  .venv\Scripts\python.exe cli.py exportar --formato excel --saida relatorio.xlsx
  .venv\Scripts\python.exe cli.py exportar --formato csv --saida relatorio.csv
  ```

### 3. Rodar os Testes Unitários
```powershell
.venv\Scripts\python.exe test_conciliator.py
```

---

## 🔑 Configuração da Chave da API Gemini (Opcional para Demonstração)
O projeto conta com modo de demonstração integrado com dados pré-configurados, permitindo testar o fluxo de conciliação e exportação sem chave.

Para leitura visual real de qualquer foto ou PDF do seu celular:
1. Copie o arquivo `.env.example` para `.env`:
   ```env
   GEMINI_API_KEY=sua_chave_aqui
   GEMINI_MODEL=gemini-2.5-flash
   ```
2. Ou insira a chave diretamente no campo da barra lateral da interface web.
