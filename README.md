# SocraticTutor-LLM

![Status](https://img.shields.io/badge/status-in%20analysis-yellow)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Groq](https://img.shields.io/badge/powered%20by-Groq-orange)

Sistema de tutoria por IA para o ensino do Problema de Monty Hall, comparando uma abordagem socrática (perguntas guiadas, sem dar a resposta) com uma abordagem expositiva (explicação direta). Este repositório contém o código do sistema, os dados anonimizados coletados e os scripts de análise usados no artigo:

> "Design e avaliação de um tutor socrático baseado em IA para o ensino de conceitos probabilísticos contraintuitivos" - Submissão feita à Revista Educação Pública / Divulgação Científica e Ensino de Ciências.

O sistema foi construído com FastAPI + Jinja2, usando a API da Groq (`llama-3.3-70b-versatile`) como modelo de linguagem, e Supabase para persistência dos dados de sessão.

---

# SocraticTutor-LLM (English)

An AI tutoring system for teaching the Monty Hall Problem, comparing a Socratic approach (guided questioning, never revealing the answer) against an expository approach (direct explanation). This repository contains the system's source code, the anonymized data collected, and the analysis scripts used in the accompanying research article (see citation above).

Built with FastAPI + Jinja2, using the Groq API (`llama-3.3-70b-versatile`) as the language model, and Supabase for session data persistence.

---

## Estrutura do repositório / Repository structure

```
TutorSocraticoLLM/
├── README.md
├── LICENSE                          # MIT
├── .env                             # variáveis de ambiente (não versionado)
├── .gitignore
├── requirements.txt
├── schema.sql                       # esquema das 4 tabelas do Supabase
│
├── app.py                           # aplicação FastAPI principal
├── classifier.py                    # classificação Paul & Elder + rubrica N0-N4
├── discourse_analysis.py            # análise de padrões discursivos pós-sessão
├── database.py                      # camada de acesso ao Supabase
│
├── templates/                       # páginas Jinja2 (idioma, consentimento, triagem, sessão, avaliação)
│   ├── language.html
│   ├── consent.html
│   ├── screening.html
│   ├── session.html
│   └── evaluation.html
│
├── docs/
│   ├── prompts.md                   # os 9 prompts de sistema usados na coleta
│   └── blind_rating_protocol.md     # protocolo de reavaliação humana cega
│
└── data/
    ├── raw/                         # exports anonimizados do Supabase (4 tabelas)
    │   ├── data_quality.md          # anomalias conhecidas nos dados brutos
    │   ├── participants_anonymized.csv
    │   ├── session_turns_anonymized.csv
    │   ├── evaluation_anonymized.csv
    │   └── session_analysis_anonymized.csv
    │
    ├── analysis/                    # tabelas agregadas e resultados dos testes estatísticos
    │   ├── caracterizacao_amostral.csv
    │   ├── concordancia_avaliadores.csv
    │   ├── comparacao_humano_vs_ia (1).csv
    │   ├── testes_estatisticos_finais (1).csv
    │   ├── group_summary.csv
    │   ├── participant_metrics.csv
    │   └── statistical_tests.json
    │
    └── figures/                     # figuras usadas no artigo
        ├── final_rubric_distribution.png
        ├── frustration_vs_turns.png
        ├── q4_frustration_by_group.png
        ├── socratic_discursive_patterns.png
        └── turn_count_by_group.png
```

---

## Anonimização / Anonymization

Todos os identificadores de participantes foram substituídos por códigos sequenciais (`P001`–`P036`) sem qualquer relação com os UUIDs originais do banco de dados. Nenhum dado pessoal identificável (nome, e-mail) foi coletado pelo sistema em nenhum momento.

All participant identifiers have been replaced with sequential codes (`P001`–`P036`), unrelated to the original database UUIDs. No personally identifiable data (name, email) was ever collected by the system.

## Ética / Ethics

Este estudo foi conduzido como pesquisa acadêmica independente, sem vínculo institucional com Comitê de Ética em Pesquisa (CEP/CONEP) no momento da coleta. Salvaguardas adotadas: consentimento livre e esclarecido, anonimização desde a origem, participação voluntária com possibilidade de interrupção a qualquer momento. Ver `docs/blind_rating_protocol.md`, Seção 9, e as Limitações do artigo para detalhes completos.

This study was conducted as independent academic research, without institutional affiliation with a Research Ethics Committee at the time of data collection. Safeguards adopted: informed consent, anonymization from the point of collection, and voluntary participation with the option to withdraw at any time. See `docs/blind_rating_protocol.md`, Section 9, and the article's Limitations section for full details.

## Licença / License

MIT License — livre para uso, modificação e distribuição, desde que mantido o aviso de copyright (ver `LICENSE`).
MIT License — free to use, modify, and distribute, as long as the copyright notice is kept (see `LICENSE`).